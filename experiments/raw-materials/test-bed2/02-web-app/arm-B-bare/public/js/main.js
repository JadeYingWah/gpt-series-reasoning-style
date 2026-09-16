/**
 * main.js — 入口：装配网络 / 渲染 / 编辑器，绑定 UI 与快捷键。
 */
import { Network } from "./network.js";
import { Renderer } from "./render.js";
import { Editor } from "./editor.js";
import { randId, throttle, toast } from "./util.js";

const canvas = document.getElementById("board");
const cursorLayer = document.getElementById("cursorLayer");

const net = new Network();
const renderer = new Renderer(canvas, cursorLayer);
const editor = new Editor(renderer, net);

/* ---------------- 连接与服务器消息 ---------------- */

net.onState = (s) => {
  const el = document.getElementById("connState");
  el.classList.remove("on", "off");
  if (s === "on") { el.textContent = "已连接"; el.classList.add("on"); }
  else if (s === "off") { el.textContent = "连接断开，重连中…"; el.classList.add("off"); }
  else el.textContent = "连接中…";
};

net.onMessage = (msg) => {
  switch (msg.t) {
    case "init": {
      renderer.shapes.clear();
      for (const s of msg.shapes) renderer.shapes.set(s.id, s);
      renderUsers(msg.users, msg.you);
      renderer.invalidate();
      break;
    }
    case "op": {
      editor.applyRemoteOp(msg.op);
      break;
    }
    case "presence": {
      renderUsers(msg.users, net.myId);
      break;
    }
    case "cursor": {
      renderer.updateCursor(msg.from, msg.name, msg.color, msg.x, msg.y);
      break;
    }
    case "draft": {
      if (msg.shape) renderer.drafts.set(msg.from, msg.shape);
      else renderer.drafts.delete(msg.from);
      renderer.invalidate();
      break;
    }
    case "error": {
      console.warn("[server]", msg.message);
      break;
    }
  }
};

/* ---------------- 用户列表 ---------------- */

function renderUsers(users, myId) {
  const ul = document.getElementById("userList");
  const count = document.getElementById("userCount");
  ul.innerHTML = "";
  let meSwatchColor = "#4f8cff";
  for (const u of users) {
    const li = document.createElement("li");
    const dot = document.createElement("span");
    dot.className = "user-dot";
    dot.style.background = u.color;
    li.appendChild(dot);
    li.appendChild(document.createTextNode(u.id === myId ? `${u.name}（我）` : u.name));
    ul.appendChild(li);
    if (u.id === myId) meSwatchColor = u.color;
  }
  count.textContent = String(users.length);
  document.getElementById("meSwatch").style.background = meSwatchColor;
}

/* ---------------- 工具栏绑定 ---------------- */

const toolButtons = [...document.querySelectorAll(".tool")];
function selectTool(tool) {
  editor.setTool(tool);
  toolButtons.forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
  canvas.style.cursor = tool === "select" ? "default" : "crosshair";
}
toolButtons.forEach((b) => b.addEventListener("click", () => selectTool(b.dataset.tool)));

const strokeColorEl = document.getElementById("strokeColor");
const fillColorEl = document.getElementById("fillColor");
const fillEnabledEl = document.getElementById("fillEnabled");
const strokeWidthEl = document.getElementById("strokeWidth");
const strokeWidthLabel = document.getElementById("strokeWidthLabel");

function pushStyle() {
  editor.setStyle({
    stroke: strokeColorEl.value,
    fill: fillColorEl.value,
    fillEnabled: fillEnabledEl.checked,
    strokeWidth: Number(strokeWidthEl.value),
  });
  strokeWidthLabel.textContent = strokeWidthEl.value;
}
[strokeColorEl, fillColorEl, fillEnabledEl, strokeWidthEl].forEach(
  (el) => el.addEventListener("input", pushStyle)
);
pushStyle();

const undoBtn = document.getElementById("undoBtn");
const redoBtn = document.getElementById("redoBtn");
editor.onHistoryChanged = (canUndo, canRedo) => {
  undoBtn.disabled = !canUndo;
  redoBtn.disabled = !canRedo;
};
undoBtn.addEventListener("click", () => editor.undo());
redoBtn.addEventListener("click", () => editor.redo());

document.getElementById("clearBtn").addEventListener("click", () => {
  if (renderer.shapes.size === 0) return;
  if (confirm("确定清空白板？此操作会同步给所有协作者（可撤销）。")) {
    editor.clearAll();
  }
});

document.getElementById("exportBtn").addEventListener("click", () => {
  const dataUrl = renderer.exportPng();
  const a = document.createElement("a");
  a.href = dataUrl;
  a.download = `whiteboard-${net.roomId || "board"}.png`;
  a.click();
  toast("已导出 PNG");
});

/* ---------------- 分享链接 ---------------- */

document.getElementById("copyLinkBtn").addEventListener("click", async () => {
  const link = location.href;
  try {
    await navigator.clipboard.writeText(link);
    toast("邀请链接已复制：" + link);
  } catch {
    // 剪贴板不可用（非 https / 权限拒绝）时退化为手动复制
    prompt("请手动复制邀请链接：", link);
  }
});

/* ---------------- 昵称 ---------------- */

const nameInput = document.getElementById("nameInput");
nameInput.value = localStorage.getItem("wb-name") || `画师-${randId(3)}`;
nameInput.addEventListener("change", () => {
  const name = nameInput.value.trim() || "访客";
  localStorage.setItem("wb-name", name);
  net.name = name;
  net.send({ t: "join", room: net.roomId, name }); // 重新 join 以更新昵称
  toast("昵称已更新");
});
net.name = nameInput.value;

/* ---------------- 画布事件 ---------------- */

canvas.addEventListener("pointerdown", (e) => editor.onPointerDown(e));
canvas.addEventListener("pointermove", throttle((e) => editor.onPointerMove(e), 16));
canvas.addEventListener("pointerup", (e) => editor.onPointerUp(e));
canvas.addEventListener("pointercancel", () => editor.onPointerUp());
canvas.addEventListener("pointerleave", () => { /* 保留拖拽状态 */ });

window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const k = e.key.toLowerCase();
  if ((e.ctrlKey || e.metaKey) && k === "z") {
    e.preventDefault();
    e.shiftKey ? editor.redo() : editor.undo();
  } else if ((e.ctrlKey || e.metaKey) && k === "y") {
    e.preventDefault();
    editor.redo();
  } else if (k === "delete" || k === "backspace") {
    e.preventDefault();
    editor.deleteSelected();
  } else if (k === "v") selectTool("select");
  else if (k === "r") selectTool("rect");
  else if (k === "o") selectTool("ellipse");
  else if (k === "a") selectTool("arrow");
  else if (k === "t") selectTool("text");
});

window.addEventListener("resize", () => renderer.resize());
renderer.resize();

/* ---------------- 启动 ---------------- */

const roomId = net.connect();
document.getElementById("roomTag").textContent = `房间：${roomId}`;
editor._notifyHistory();
