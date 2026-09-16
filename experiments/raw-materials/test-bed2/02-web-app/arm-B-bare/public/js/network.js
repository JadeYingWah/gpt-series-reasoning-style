/**
 * network.js — WebSocket 客户端：连接管理、自动重连、消息派发。
 */
import { randId } from "./util.js";

const RECONNECT_BASE_MS = 800;
const RECONNECT_MAX_MS = 5000;

export class Network {
  constructor() {
    /** @type {WebSocket|null} */
    this.ws = null;
    this.roomId = null;
    this.myId = null;
    this.myColor = "#888";
    this.joined = false;
    this.closedByUser = false;
    this._retry = 0;
    this._timer = null;

    /** @type {(msg: object) => void} 由 main 注入 */
    this.onMessage = null;
    /** @type {(state: "connecting"|"on"|"off") => void} */
    this.onState = null;
  }

  /** 解析/生成房间号并连接。返回 roomId。 */
  connect() {
    const url = new URL(location.href);
    let room = url.searchParams.get("room");
    if (!room || !/^[A-Za-z0-9_-]{4,32}$/.test(room)) {
      room = randId(8);
      url.searchParams.set("room", room);
      history.replaceState(null, "", url);
    }
    this.roomId = room;

    const proto = location.protocol === "https:" ? "wss://" : "ws://";
    this._open(`${proto}${location.host}/ws`);
    return room;
  }

  _open(url) {
    this._setState("connecting");
    const ws = new WebSocket(url);
    this.ws = ws;

    ws.onopen = () => {
      this._retry = 0;
      this.send({ t: "join", room: this.roomId, name: this.name || "访客" });
    };

    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch { return; }
      if (msg.t === "init") {
        this.joined = true;
        this.myId = msg.you;
        this.myColor = msg.color;
      }
      if (this.onMessage) this.onMessage(msg);
    };

    ws.onclose = () => {
      this.joined = false;
      if (this.closedByUser) return;
      this._setState("off");
      this._scheduleReconnect();
    };

    ws.onerror = () => {
      try { ws.close(); } catch { /* ignore */ }
    };
  }

  _scheduleReconnect() {
    const delay = Math.min(RECONNECT_BASE_MS * 2 ** this._retry, RECONNECT_MAX_MS);
    this._retry++;
    clearTimeout(this._timer);
    this._timer = setTimeout(() => this._open(this.ws.url ?? this._lastUrl()), delay);
  }

  _lastUrl() {
    const proto = location.protocol === "https:" ? "wss://" : "ws://";
    return `${proto}${location.host}/ws`;
  }

  _setState(s) {
    if (this.onState) this.onState(s);
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
      return true;
    }
    return false;
  }

  sendOp(op) {
    return this.send({ t: "op", op });
  }

  sendCursorThrottled(x, y) {
    const now = Date.now();
    if (now - (this._lastCursorAt || 0) < 60) return;
    this._lastCursorAt = now;
    this.send({ t: "cursor", x, y });
  }

  sendDraft(shape) {
    return this.send({ t: "draft", shape });
  }

  close() {
    this.closedByUser = true;
    clearTimeout(this._timer);
    if (this.ws) try { this.ws.close(); } catch { /* ignore */ }
  }
}
