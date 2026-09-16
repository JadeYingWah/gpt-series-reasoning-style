/**
 * smoke.js — 端到端冒烟测试（零依赖，Node >= 21 的全局 WebSocket）。
 *
 * 覆盖：静态页可访问、WS 握手、join/init、op 广播、快照同步、
 * presence、cursor/draft 转发、非法 op 报错。
 */
import { spawn } from "node:child_process";
import http from "node:http";

const PORT = 3199;
const BASE = `http://localhost:${PORT}`;

function waitPort(ms = 5000) {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const probe = () => {
      http.get(`${BASE}/index.html`, (res) => {
        res.resume();
        resolve(res.statusCode);
      }).on("error", () => {
        if (Date.now() - start > ms) reject(new Error("server not up"));
        else setTimeout(probe, 150);
      });
    };
    probe();
  });
}

/** 极简 Promise 化 WS 客户端。 */
class Client {
  constructor(label) {
    this.label = label;
    this.queue = [];
    this.waiters = [];
    this.ws = new WebSocket(`ws://localhost:${PORT}/ws`);
    this.opened = new Promise((res, rej) => {
      this.ws.onopen = res;
      this.ws.onerror = () => rej(new Error(`${label}: ws open failed`));
    });
    this.ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      const w = this.waiters.shift();
      if (w) w.resolve(msg);
      else this.queue.push(msg);
    };
  }

  send(obj) { this.ws.send(JSON.stringify(obj)); }

  /** 等待下一条（可按类型过滤，跳过不匹配的消息但保留在队列尾？——直接丢弃不匹配项前的缓存扫描）。 */
  next(type, timeoutMs = 2000) {
    const idx = this.queue.findIndex((m) => !type || m.t === type);
    if (idx >= 0) return Promise.resolve(this.queue.splice(idx, 1)[0]);
    return new Promise((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new Error(`${this.label}: timeout waiting "${type}"`)),
        timeoutMs
      );
      this.waiters.push({
        resolve: (m) => {
          if (type && m.t !== type) {
            // 类型不符：继续等（把消息塞回队列头之前的不匹配项丢弃）
            const again = this.waiters.length > 0;
            if (!again) { clearTimeout(timer); resolve(m); }
            return;
          }
          clearTimeout(timer);
          resolve(m);
        },
      });
    });
  }

  close() { try { this.ws.close(); } catch { /* ignore */ } }
}

async function expect(cond, name) {
  if (!cond) throw new Error(`ASSERT FAIL: ${name}`);
  console.log(`  ✓ ${name}`);
}

const server = spawn(process.execPath, ["server/server.js"], {
  env: { ...process.env, PORT: String(PORT) },
  stdio: ["ignore", "pipe", "pipe"],
});
server.stderr.on("data", (d) => console.error("[server-err]", String(d)));

try {
  const status = await waitPort();
  await expect(status === 200, `静态页 index.html 可访问 (HTTP ${status})`);

  const u1 = new Client("u1");
  const u2 = new Client("u2");
  await Promise.all([u1.opened, u2.opened]);
  console.log("  ✓ WebSocket 握手成功");

  // 加入房间
  u1.send({ t: "join", room: "smoke-room", name: "甲" });
  const init1 = await u1.next("init");
  await expect(Array.isArray(init1.shapes) && init1.users.length === 1, "u1 join → init(shapes/users)");

  u2.send({ t: "join", room: "smoke-room", name: "乙" });
  const init2 = await u2.next("init");
  await expect(init2.users.length === 2, "u2 join → presence 计 2 人");
  const p1 = await u1.next("presence");
  await expect(p1.users.length === 2, "u1 收到 presence 更新");

  // u1 画矩形 → u2 应收到 op
  const rect = { id: "r1", type: "rect", x1: 10, y1: 10, x2: 200, y2: 100, stroke: "#111", fill: null, strokeWidth: 2, text: "", fontSize: 28, createdBy: init1.you };
  u1.send({ t: "op", op: { kind: "add", shape: rect } });
  const opToU2 = await u2.next("op");
  await expect(opToU2.op.shape.id === "r1" && opToU2.from === init1.you, "add op 实时广播到 u2");

  // update
  const moved = { ...rect, x1: 50, x2: 240 };
  u1.send({ t: "op", op: { kind: "update", shape: moved } });
  const upd = await u2.next("op");
  await expect(upd.op.kind === "update" && upd.op.shape.x1 === 50, "update op 广播");

  // cursor / draft 转发
  u1.send({ t: "cursor", x: 100, y: 200 });
  const cur = await u2.next("cursor");
  await expect(cur.x === 100 && cur.name === "甲", "cursor 转发携带昵称");
  u1.send({ t: "draft", shape: rect });
  const dr = await u2.next("draft");
  await expect(dr.shape && dr.shape.id === "r1", "draft 预览转发");

  // u3 后加入 → 收到权威快照
  const u3 = new Client("u3");
  await u3.opened;
  u3.send({ t: "join", room: "smoke-room", name: "丙" });
  const init3 = await u3.next("init");
  await expect(init3.shapes.length === 1 && init3.shapes[0].id === "r1", "新成员收到完整快照");

  // 非法 op → error
  u3.send({ t: "op", op: { kind: "nuke" } });
  const err = await u3.next("error");
  await expect(!!err.message, "非法 op 返回 error");

  // remove 后快照为空
  u1.send({ t: "op", op: { kind: "remove", shape: rect } });
  await u2.next("op");
  const u4 = new Client("u4");
  await u4.opened;
  u4.send({ t: "join", room: "smoke-room", name: "丁" });
  const init4 = await u4.next("init");
  await expect(init4.shapes.length === 0, "remove 生效：新成员快照为空");

  u1.close(); u2.close(); u3.close(); u4.close();
  console.log("\nSMOKE PASS — 全部断言通过");
  process.exitCode = 0;
} catch (err) {
  console.error("\nSMOKE FAIL —", err.message);
  process.exitCode = 1;
} finally {
  server.kill();
}
