'use strict';
/**
 * 协作白板服务端
 * - HTTP：托管 public/ 静态文件
 * - WebSocket（/ws）：房间广播、形状状态同步、在线光标、心跳保活
 * 房间内容保存在内存中（服务运行期间有效），迟加入者通过 init 获得全量状态。
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { WebSocketServer } = require('ws');

const PORT = Number(process.env.PORT) || 3000;
const HOST = process.env.HOST || '0.0.0.0';
const DEBUG = process.env.WS_DEBUG === '1';
function dbg(...args) { if (DEBUG) console.log('[ws-debug]', ...args); }
const PUBLIC_DIR = path.join(__dirname, 'public');
const MAX_SHAPES_PER_ROOM = 3000;
const MAX_ROOMS = 500;
const MAX_POINTS = 5000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
  '.json': 'application/json; charset=utf-8',
};

// ---------------- HTTP 静态服务 ----------------
const server = http.createServer((req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let pathname;
    try { pathname = decodeURIComponent(url.pathname); } catch { pathname = url.pathname; }
    if (pathname === '/') pathname = '/index.html';
    const filePath = path.normalize(path.join(PUBLIC_DIR, pathname));
    if (!filePath.startsWith(PUBLIC_DIR)) {
      res.writeHead(403, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end('Forbidden');
      return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
        res.end('Not Found');
        return;
      }
      const ext = path.extname(filePath).toLowerCase();
      res.writeHead(200, {
        'Content-Type': MIME[ext] || 'application/octet-stream',
        'Cache-Control': 'no-cache',
      });
      res.end(data);
    });
  } catch (e) {
    res.writeHead(400, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('Bad Request');
  }
});

// ---------------- 房间状态 ----------------
// rooms: roomId -> { shapes: Map<id, shape>, clients: Map<ws, user>, seq }
const rooms = new Map();

const PALETTE = ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71', '#1abc9c', '#3498db', '#9b59b6', '#e91e63'];

function randId(n) { return crypto.randomBytes(n).toString('hex'); }

function getRoom(id) {
  let room = rooms.get(id);
  if (!room) {
    if (rooms.size >= MAX_ROOMS) {
      for (const [rid, r] of rooms) {
        if (r.clients.size === 0) { rooms.delete(rid); break; }
      }
    }
    room = { shapes: new Map(), clients: new Map(), seq: 0 };
    rooms.set(id, room);
  }
  return room;
}

// ---------------- 输入校验 ----------------
function sanitizeRoomId(r) {
  return (typeof r === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(r)) ? r : null;
}
function isHexColor(c) { return typeof c === 'string' && /^#[0-9a-fA-F]{3,8}$/.test(c); }
function num(v, min, max) {
  v = Number(v);
  if (!Number.isFinite(v)) return null;
  return Math.min(max, Math.max(min, v));
}
function clampCoord(v) { return num(v, -10000, 30000); }

function sanitizeShape(raw) {
  if (!raw || typeof raw !== 'object') return null;
  const id = (typeof raw.id === 'string' && /^[A-Za-z0-9_-]{1,64}$/.test(raw.id)) ? raw.id : null;
  if (!id) return null;
  const color = isHexColor(raw.color) ? raw.color : '#1e293b';
  const width = num(raw.width, 1, 60) || 3;
  const out = { id, color, width };
  switch (raw.type) {
    case 'rect':
    case 'ellipse': {
      const x = clampCoord(raw.x), y = clampCoord(raw.y);
      const w = num(raw.w, -30000, 30000), h = num(raw.h, -30000, 30000);
      if (x == null || y == null || w == null || h == null) return null;
      out.type = raw.type; out.x = x; out.y = y; out.w = w; out.h = h;
      return out;
    }
    case 'arrow': {
      const x1 = clampCoord(raw.x1), y1 = clampCoord(raw.y1);
      const x2 = clampCoord(raw.x2), y2 = clampCoord(raw.y2);
      if (x1 == null || y1 == null || x2 == null || y2 == null) return null;
      out.type = 'arrow'; out.x1 = x1; out.y1 = y1; out.x2 = x2; out.y2 = y2;
      return out;
    }
    case 'text': {
      const x = clampCoord(raw.x), y = clampCoord(raw.y);
      const size = num(raw.size, 8, 300);
      const text = (typeof raw.text === 'string' && raw.text.length >= 1 && raw.text.length <= 2000) ? raw.text : null;
      if (x == null || y == null || size == null || !text) return null;
      out.type = 'text'; out.x = x; out.y = y; out.size = size; out.text = text;
      out.w = num(raw.w, 0, 30000) || 0;
      out.h = num(raw.h, 0, 30000) || 0;
      return out;
    }
    case 'pencil': {
      if (!Array.isArray(raw.points) || raw.points.length < 1 || raw.points.length > MAX_POINTS) return null;
      const pts = [];
      for (const pt of raw.points) {
        if (!Array.isArray(pt) || pt.length < 2) return null;
        const x = clampCoord(pt[0]), y = clampCoord(pt[1]);
        if (x == null || y == null) return null;
        pts.push([x, y]);
      }
      out.type = 'pencil'; out.points = pts;
      return out;
    }
    default:
      return null;
  }
}

// ---------------- WebSocket ----------------
const wss = new WebSocketServer({ server, path: '/ws', maxPayload: 1024 * 1024 });

function send(ws, obj) {
  if (ws.readyState === 1) { try { ws.send(JSON.stringify(obj)); } catch (e) { /* ignore */ } }
}
function broadcast(room, obj, excludeWs) {
  const data = JSON.stringify(obj);
  let n = 0;
  for (const client of room.clients.keys()) {
    if (client === excludeWs) continue;
    if (client.readyState === 1) {
      try { client.send(data); n++; } catch (e) { /* ignore */ }
    }
  }
  dbg('broadcast', obj.type, '->', n, 'clients');
}

wss.on('connection', (ws) => {
  ws.isAlive = true;
  ws.on('pong', () => { ws.isAlive = true; });
  let joined = false;
  let roomId = null;
  let user = null;
  dbg('connection opened');

  ws.on('message', (data) => {
    let msg;
    try { msg = JSON.parse(data.toString()); } catch (e) { dbg('malformed json'); return; }
    if (!msg || typeof msg !== 'object') return;
    dbg('msg from', user ? user.name : 'unjoined', ':', msg.type);

    // 首条消息必须是 join
    if (!joined) {
      if (msg.type !== 'join') return;
      const rid = sanitizeRoomId(msg.room);
      if (!rid) { send(ws, { type: 'error', message: '无效的房间号' }); return; }
      const room = getRoom(rid);
      roomId = rid;
      user = {
        id: randId(8),
        name: '用户' + (room.seq + 1),
        color: PALETTE[room.seq % PALETTE.length],
      };
      room.seq += 1;
      room.clients.set(ws, user);
      joined = true;
      send(ws, {
        type: 'init',
        selfId: user.id,
        roomId,
        shapes: [...room.shapes.values()],
        users: [...room.clients.values()].map((u) => ({ id: u.id, name: u.name, color: u.color })),
      });
      broadcast(room, { type: 'user-joined', user }, ws);
      return;
    }

    const room = rooms.get(roomId);
    if (!room) return;

    switch (msg.type) {
      case 'add': {
        const s = sanitizeShape(msg.shape);
        if (!s) { dbg('add rejected: invalid shape', JSON.stringify(msg.shape).slice(0, 200)); send(ws, { type: 'error', message: '无效的图形数据' }); return; }
        if (room.shapes.has(s.id)) return;
        if (room.shapes.size >= MAX_SHAPES_PER_ROOM) {
          send(ws, { type: 'error', message: '画板内容已达上限，无法继续添加' });
          return;
        }
        s.by = user.id;
        room.shapes.set(s.id, s);
        broadcast(room, { type: 'add', shape: s }, ws);
        break;
      }
      case 'update': {
        const s = sanitizeShape(msg.shape);
        if (!s) return;
        const cur = room.shapes.get(s.id);
        if (!cur) return;
        s.by = cur.by;
        room.shapes.set(s.id, s);
        broadcast(room, { type: 'update', shape: s }, ws);
        break;
      }
      case 'delete': {
        if (typeof msg.id !== 'string' || !/^[A-Za-z0-9_-]{1,64}$/.test(msg.id)) return;
        if (room.shapes.delete(msg.id)) broadcast(room, { type: 'delete', id: msg.id }, ws);
        break;
      }
      case 'clear': {
        room.shapes.clear();
        broadcast(room, { type: 'clear' }, ws);
        break;
      }
      case 'cursor': {
        const x = num(msg.x, -10000, 30000), y = num(msg.y, -10000, 30000);
        if (x == null || y == null) return;
        broadcast(room, { type: 'cursor', id: user.id, name: user.name, color: user.color, x, y }, ws);
        break;
      }
      default:
        break; // 未知消息类型静默忽略
    }
  });

  ws.on('close', () => {
    if (roomId && user) {
      const room = rooms.get(roomId);
      if (room) {
        room.clients.delete(ws);
        broadcast(room, { type: 'user-left', id: user.id });
      }
    }
  });
  ws.on('error', () => { try { ws.close(); } catch (e) { /* ignore */ } });
});

// 心跳保活：30s 无 pong 则断开
const heartbeat = setInterval(() => {
  for (const ws of wss.clients) {
    if (ws.isAlive === false) { ws.terminate(); continue; }
    ws.isAlive = false;
    try { ws.ping(); } catch (e) { /* ignore */ }
  }
}, 30000);
wss.on('close', () => clearInterval(heartbeat));

server.listen(PORT, HOST, () => {
  console.log(`[whiteboard] 服务已启动: http://localhost:${PORT}`);
  console.log(`[whiteboard] WebSocket 端点: ws://localhost:${PORT}/ws`);
});
