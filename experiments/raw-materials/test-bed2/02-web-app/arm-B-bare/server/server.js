/**
 * server.js — 协作白板服务器入口。
 *
 * 职责：
 *  1. HTTP 静态文件服务（public/）
 *  2. 接收 WebSocket 升级请求
 *  3. 房间管理：join / op 应用 / 广播 / 在线用户 presence
 *
 * 协议（JSON 文本帧）：
 *  客户端→服务器：
 *    { t:"join", room, name }
 *    { t:"op", op:{ kind:"add"|"update"|"remove", shape } }
 *    { t:"cursor", x, y }            // 世界坐标
 *    { t:"draft", shape|null }       // 正在绘制的预览
 *  服务器→客户端：
 *    { t:"init", you, color, shapes, users }
 *    { t:"op", op, from }
 *    { t:"presence", users }
 *    { t:"cursor", from, name, color, x, y }
 *    { t:"draft", from, name, color, shape }
 *    { t:"error", message }
 *
 * 状态为内存态（重启清空），op 语义 last-write-wins。
 */
import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { acceptUpgrade } from "./websocket.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PUBLIC_DIR = path.join(__dirname, "..", "public");
const PORT = Number(process.env.PORT || 3000);

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

/* ---------------- 房间状态 ---------------- */

/** rooms: Map<roomId, { shapes: Map<id, shape>, clients: Set<Client> }> */
const rooms = new Map();

function getRoom(roomId) {
  let room = rooms.get(roomId);
  if (!room) {
    room = { shapes: new Map(), clients: new Set() };
    rooms.set(roomId, room);
  }
  return room;
}

const USERS_COLORS = [
  "#e74c3c", "#3498db", "#2ecc71", "#9b59b6",
  "#f39c12", "#1abc9c", "#e67e22", "#16a085",
];

function pickColor(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  return USERS_COLORS[h % USERS_COLORS.length];
}

function roomUserList(room) {
  return [...room.clients].map((c) => ({
    id: c.id,
    name: c.name,
    color: c.color,
  }));
}

function broadcast(room, msg, exclude) {
  const text = JSON.stringify(msg);
  for (const client of room.clients) {
    if (client !== exclude) client.conn.sendText(text);
  }
}

/** 应用一个 op 到房间权威状态；非法 op 返回 null。 */
function applyOp(room, op) {
  if (!op || typeof op !== "object" || !op.kind || !op.shape) return false;
  const s = op.shape;
  if (!s || typeof s.id !== "string" || s.id.length > 64) return false;
  if (op.kind === "add" || op.kind === "update") {
    if (!s.type) return false;
    room.shapes.set(s.id, s);
    return true;
  }
  if (op.kind === "remove") {
    room.shapes.delete(s.id);
    return true;
  }
  return false;
}

/* ---------------- WebSocket 会话 ---------------- */

function onUpgrade(req, socket) {
  const conn = acceptUpgrade(req, socket);
  if (!conn) return;

  const client = {
    conn,
    id: null,
    name: "",
    color: "#888",
    room: null,
  };

  conn.onMessage = (text) => {
    let msg;
    try {
      msg = JSON.parse(text);
    } catch {
      conn.sendJson({ t: "error", message: "invalid json" });
      return;
    }
    try { handle(client, msg); } catch (err) {
      conn.sendJson({ t: "error", message: String((err && err.message) || err) });
    }
  };

  conn.onClose = () => {
    if (client.room) {
      client.room.clients.delete(client);
      broadcast(client.room, {
        t: "presence",
        users: roomUserList(client.room),
      });
    }
  };

  // 空闲保活：每 30s ping 一次，写失败时连接会被标记关闭
  const heartbeat = setInterval(() => {
    if (!conn.alive) {
      clearInterval(heartbeat);
      return;
    }
    conn._ping();
  }, 30000);
  conn.socket.on("close", () => clearInterval(heartbeat));
}

function handle(client, msg) {
  switch (msg.t) {
    case "join": {
      const roomId = typeof msg.room === "string" ? msg.room.slice(0, 64) : "";
      if (!roomId) return fail(client, "missing room");
      const name = typeof msg.name === "string" && msg.name.trim()
        ? msg.name.trim().slice(0, 24)
        : "访客";
      if (client.room) client.room.clients.delete(client);

      client.id = cryptoId();
      client.name = name;
      client.color = pickColor(client.id);
      client.room = getRoom(roomId);
      client.room.clients.add(client);

      client.conn.sendJson({
        t: "init",
        you: client.id,
        color: client.color,
        shapes: [...client.room.shapes.values()],
        users: roomUserList(client.room),
      });
      broadcast(client.room, {
        t: "presence",
        users: roomUserList(client.room),
      }, client);
      return;
    }

    case "op": {
      if (!client.room) return fail(client, "join first");
      const op = msg.op;
      if (!applyOp(client.room, op)) return fail(client, "bad op");
      // 转发时附带发送者，供客户端做“只撤自己的”历史过滤
      broadcast(client.room, { t: "op", op, from: client.id }, client);
      return;
    }

    case "cursor": {
      if (!client.room) return;
      const x = Number(msg.x), y = Number(msg.y);
      if (!Number.isFinite(x) || !Number.isFinite(y)) return;
      broadcast(client.room, {
        t: "cursor", from: client.id, name: client.name,
        color: client.color, x, y,
      }, client);
      return;
    }

    case "draft": {
      if (!client.room) return;
      broadcast(client.room, {
        t: "draft", from: client.id, name: client.name,
        color: client.color, shape: msg.shape ?? null,
      }, client);
      return;
    }

    default:
      fail(client, `unknown message type: ${String(msg.t)}`);
  }
}

function fail(client, message) {
  client.conn.sendJson({ t: "error", message });
}

function cryptoId() {
  return Math.random().toString(36).slice(2, 10) + Date.now().toString(36).slice(-4);
}

/* ---------------- HTTP 静态服务 ---------------- */

function serveStatic(req, res) {
  const url = new URL(req.url, "http://localhost");
  let filePath = url.pathname === "/" ? "/index.html" : url.pathname;
  filePath = path.normalize(filePath).replace(/^(\.\.[/\\])+/, "");
  const abs = path.join(PUBLIC_DIR, filePath);
  if (!abs.startsWith(PUBLIC_DIR)) {
    res.writeHead(403).end("forbidden");
    return;
  }
  fs.readFile(abs, (err, data) => {
    if (err) {
      res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("404 Not Found");
      return;
    }
    const ext = path.extname(abs).toLowerCase();
    res.writeHead(200, { "Content-Type": MIME[ext] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer(serveStatic);
server.on("upgrade", onUpgrade);

server.listen(PORT, () => {
  console.log(`[whiteboard] listening on http://localhost:${PORT}`);
});

/* 供冒烟测试动态导入使用 */
export { server, rooms };
