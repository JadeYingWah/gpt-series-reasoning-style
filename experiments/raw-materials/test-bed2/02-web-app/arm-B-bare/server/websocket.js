/**
 * websocket.js — 零依赖的最小 WebSocket 服务端实现（RFC 6455 子集）。
 *
 * 覆盖：握手(101)、text 帧、分片(continuation)、close、ping/pong、
 * 7-bit / 16-bit / 64-bit 三种 payload 长度。客户端→服务端帧必须 unmask。
 * 仅收发小体积 JSON 文本，不做 permessage-deflate 扩展。
 */
import crypto from "node:crypto";

const GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

/** 对一次 HTTP upgrade 完成握手，返回可收发帧的连接对象。 */
export function acceptUpgrade(req, socket) {
  const key = req.headers["sec-websocket-key"];
  if (!key) {
    socket.destroy();
    return null;
  }
  const accept = crypto
    .createHash("sha1")
    .update(key + GUID)
    .digest("base64");
  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\n" +
      "Upgrade: websocket\r\n" +
      "Connection: Upgrade\r\n" +
      `Sec-WebSocket-Accept: ${accept}\r\n` +
      "\r\n"
  );
  socket.setNoDelay(true);
  return new WsConnection(socket);
}

export class WsConnection {
  constructor(socket) {
    this.socket = socket;
    this.alive = true;
    this.onMessage = null; // (text: string) => void
    this.onClose = null;   // () => void
    this._buf = Buffer.alloc(0);
    this._fragments = [];
    this._fragOpcode = 0;

    socket.on("data", (chunk) => this._feed(chunk));
    const die = () => this._closed();
    socket.on("close", die);
    socket.on("error", die);
    socket.on("end", die);
  }

  /** 发送一条文本帧（服务端→客户端不 mask）。 */
  sendText(text) {
    if (!this.alive) return;
    this.socket.write(encodeFrame(0x1, Buffer.from(text, "utf8")));
  }

  sendJson(obj) {
    this.sendText(JSON.stringify(obj));
  }

  /** 主动关闭：发 close 帧后尽快结束 TCP。 */
  close() {
    if (!this.alive) return;
    try {
      this.socket.write(encodeFrame(0x8, Buffer.alloc(0)));
    } catch { /* socket 已坏，忽略 */ }
    this.socket.end();
    this._closed();
  }

  _ping() {
    if (this.alive) {
      try { this.socket.write(encodeFrame(0x9, Buffer.alloc(0))); } catch { /* ignore */ }
    }
  }

  _feed(chunk) {
    this._buf = Buffer.concat([this._buf, chunk]);
    while (true) {
      const frame = decodeFrame(this._buf);
      if (!frame) break; // 数据不完整，等下一块
      this._buf = this._buf.subarray(frame.totalLen);
      this._handle(frame);
    }
  }

  _handle(frame) {
    if (frame.opcode === 0x8) { // close
      this.close();
      return;
    }
    if (frame.opcode === 0x9) { // ping → pong
      try { this.socket.write(encodeFrame(0xA, frame.payload)); } catch { /* ignore */ }
      return;
    }
    if (frame.opcode === 0xA) return; // pong：保活即可

    const isData = frame.opcode === 0x1 || frame.opcode === 0x2 || frame.opcode === 0x0;
    if (!isData) return;

    if (frame.opcode !== 0x0) { // 新消息起始
      this._fragOpcode = frame.opcode;
      this._fragments = [frame.payload];
    } else {
      this._fragments.push(frame.payload);
    }
    if (frame.fin) {
      const text = Buffer.concat(this._fragments).toString("utf8");
      this._fragments = [];
      this._fragOpcode = 0;
      if (this.onMessage) this.onMessage(text);
    }
  }

  _closed() {
    if (!this.alive) return;
    this.alive = false;
    try { this.socket.destroy(); } catch { /* ignore */ }
    if (this.onClose) this.onClose();
  }
}

/** 解析缓冲区最前面的一个帧；数据不完整时返回 null。 */
function decodeFrame(buf) {
  if (buf.length < 2) return null;
  const first = buf[0];
  const second = buf[1];
  const fin = (first & 0x80) !== 0;
  const opcode = first & 0x0f;
  const masked = (second & 0x80) !== 0;
  let len = second & 0x7f;
  let offset = 2;

  if (len === 126) {
    if (buf.length < offset + 2) return null;
    len = buf.readUInt16BE(offset);
    offset += 2;
  } else if (len === 127) {
    if (buf.length < offset + 8) return null;
    const big = buf.readBigUInt64BE(offset);
    if (big > BigInt(Number.MAX_SAFE_INTEGER)) return null;
    len = Number(big);
    offset += 8;
  }

  let maskKey = null;
  if (masked) {
    if (buf.length < offset + 4) return null;
    maskKey = buf.subarray(offset, offset + 4);
    offset += 4;
  }
  if (buf.length < offset + len) return null;

  let payload = buf.subarray(offset, offset + len);
  if (maskKey) {
    payload = Buffer.from(payload); // 复制后再 unmask，避免污染原缓冲
    for (let i = 0; i < payload.length; i++) {
      payload[i] ^= maskKey[i % 4];
    }
  }
  return { fin, opcode, payload, totalLen: offset + len };
}

/** 编码一个服务端发出的帧。 */
function encodeFrame(opcode, payload) {
  const len = payload.length;
  let header;
  if (len < 126) {
    header = Buffer.from([0x80 | opcode, len]);
  } else if (len < 65536) {
    header = Buffer.alloc(4);
    header[0] = 0x80 | opcode;
    header[1] = 126;
    header.writeUInt16BE(len, 2);
  } else {
    header = Buffer.alloc(10);
    header[0] = 0x80 | opcode;
    header[1] = 127;
    header.writeBigUInt64BE(BigInt(len), 2);
  }
  return Buffer.concat([header, payload]);
}
