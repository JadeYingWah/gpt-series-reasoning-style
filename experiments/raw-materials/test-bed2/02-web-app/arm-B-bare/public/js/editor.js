/**
 * editor.js — 画布交互核心：工具状态机、op 提交与应用、撤销/重做、文字编辑。
 */
import {
  makeShape, pickShape, translateShape, boundsOf,
  measureTextWidth, drawShape,
} from "./shapes.js";
import { History } from "./history.js";
import { randId } from "./util.js";

export class Editor {
  /**
   * @param {import("./render.js").Renderer} renderer
   * @param {import("./network.js").Network} net
   */
  constructor(renderer, net) {
    this.renderer = renderer;
    this.net = net;

    this.tool = "select";
    this.strokeColor = "#1e88e5";
    this.fillColor = "#ffffff";
    this.fillEnabled = false;
    this.strokeWidth = 2;

    this.history = new History();
    this.selectedId = null;

    // 拖拽/绘制状态
    this._drag = null;      // { mode:"draw"|"move"|"pan", ... }
    this._myDraft = null;

    this.onHistoryChanged = null; // 供 UI 刷新撤销/重做按钮
  }

  /* ================= op 提交与应用 ================= */

  /** 本地应用 op 并广播。update 需传 prevShape 供撤销。 */
  commit(op, prevShape = null) {
    this._applyLocal(op);
    if (op.kind === "add" || op.kind === "update" || op.kind === "remove") {
      this.history.push(op, prevShape);
      this._notifyHistory();
    }
    this.net.sendOp(op);
    this.renderer.invalidate();
  }

  /** 收到本人 op 的服务器回显：状态已本地应用过，只补历史。
   *  （本实现为乐观应用：本地先改，广播即达；服务器转发给“其他人”。） */
  applyRemoteOp(op) {
    this._applyLocal(op);
    this.renderer.invalidate();
  }

  _applyLocal(op) {
    const shapes = this.renderer.shapes;
    if (op.kind === "add" || op.kind === "update") {
      shapes.set(op.shape.id, op.shape);
    } else if (op.kind === "remove") {
      shapes.delete(op.shape.id);
      if (this.selectedId === op.shape.id) this.selectedId = null;
    }
  }

  undo() {
    const op = this.history.popUndo();
    if (!op) return;
    this._applyLocal(op);
    this.net.sendOp(op);
    this._notifyHistory();
    this.renderer.invalidate();
  }

  redo() {
    const op = this.history.popRedo();
    if (!op) return;
    this._applyLocal(op);
    this.net.sendOp(op);
    this._notifyHistory();
    this.renderer.invalidate();
  }

  /** 清空：把当前所有图形逐一 remove 提交（作为一组，撤销可整体恢复）。 */
  clearAll() {
    const all = [...this.renderer.shapes.values()];
    if (all.length === 0) return;
    for (const s of all) {
      this._applyLocal({ kind: "remove", shape: s });
      this.net.sendOp({ kind: "remove", shape: s });
      this.history.push({ kind: "remove", shape: s }, null);
    }
    this.selectedId = null;
    this._notifyHistory();
    this.renderer.invalidate();
  }

  _notifyHistory() {
    if (this.onHistoryChanged) {
      this.onHistoryChanged(this.history.canUndo(), this.history.canRedo());
    }
  }

  /* ================= 指针事件 ================= */

  onPointerDown(e) {
    const canvas = this.renderer.canvas;
    canvas.setPointerCapture(e.pointerId);
    const w = this.renderer.toWorld(e.clientX, e.clientY);

    if (this.tool === "select") {
      const id = pickShape(this.renderer.shapes, w.x, w.y);
      this.selectedId = id;
      if (id) {
        const s = this.renderer.shapes.get(id);
        this._drag = { mode: "move", id, startX: w.x, startY: w.y, orig: { ...s } };
      }
      this.renderer.invalidate();
      return;
    }

    if (this.tool === "text") {
      this._beginTextEdit(w);
      return;
    }

    // 绘制类工具
    this._drag = { mode: "draw", startX: w.x, startY: w.y };
    this._myDraft = makeShape(this.tool, randId(10), w.x, w.y, w.x, w.y, {
      stroke: this.strokeColor,
      fill: this.fillEnabled ? this.fillColor : null,
      strokeWidth: this.strokeWidth,
      createdBy: this.net.myId,
    });
    this.renderer.invalidate();
  }

  onPointerMove(e) {
    const w = this.renderer.toWorld(e.clientX, e.clientY);
    this.net.sendCursorThrottled(w.x, w.y);

    if (!this._drag) return;

    if (this._drag.mode === "draw") {
      const d = this._myDraft;
      // 文字先占位（字号行高），真正内容由 text tool 输入
      d.x2 = w.x; d.y2 = w.y;
      this.net.sendDraft(d);
      this.renderer.invalidate();
      return;
    }

    if (this._drag.mode === "move") {
      const s = this.renderer.shapes.get(this._drag.id);
      if (!s) return;
      const dx = w.x - this._drag.startX;
      const dy = w.y - this._drag.startY;
      // 从 orig 拷贝避免累积误差
      const moved = { ...this._drag.orig };
      translateShape(moved, dx, dy);
      shapesReplace(this.renderer.shapes, s, moved);
      this.net.sendOp({ kind: "update", shape: moved });
      this.renderer.invalidate();
    }
  }

  onPointerUp() {
    if (!this._drag) return;
    const drag = this._drag;
    this._drag = null;

    if (drag.mode === "draw") {
      const d = this._myDraft;
      this._myDraft = null;
      this.net.sendDraft(null);
      const b = boundsOf(d);
      const tooSmall = b.w < 4 && b.h < 4 && d.type !== "text";
      if (tooSmall) { this.renderer.invalidate(); return; }
      this.commit({ kind: "add", shape: d });
      return;
    }

    if (drag.mode === "move") {
      const prev = drag.orig;
      const s = this.renderer.shapes.get(drag.id);
      if (s && (s.x1 !== prev.x1 || s.y1 !== prev.y1 || s.x2 !== prev.x2 || s.y2 !== prev.y2)) {
        this.history.push({ kind: "update", shape: { ...s } }, prev);
        this._notifyHistory();
      }
    }
  }

  /** Delete 键删除选中图形。 */
  deleteSelected() {
    if (!this.selectedId) return;
    const s = this.renderer.shapes.get(this.selectedId);
    if (!s) return;
    this.commit({ kind: "remove", shape: s });
    this.selectedId = null;
  }

  /* ================= 文字工具 ================= */

  _beginTextEdit(w) {
    const { renderer } = this;
    const input = document.getElementById("textEditor");
    input.style.display = "block";
    const p = renderer.worldToCss(w.x, w.y);
    input.style.left = `${p.x}px`;
    input.style.top = `${p.y}px`;
    input.value = "";
    input.focus();

    const finish = (commit) => {
      input.style.display = "none";
      input.onkeydown = null;
      input.onblur = null;
      const text = input.value.trim();
      if (commit && text) {
        // 让屏幕上看到的文字高度接近输入框字号（16px CSS）
        const fontSize = Math.min(64, Math.max(18, Math.round(16 / renderer.cssScale)));
        const shape = makeShape("text", randId(10), w.x, w.y - fontSize * 0.7, w.x, w.y, {
          stroke: this.strokeColor,
          strokeWidth: this.strokeWidth,
          text,
          fontSize,
          createdBy: this.net.myId,
        });
        this.commit({ kind: "add", shape });
      }
    };
    input.onkeydown = (ev) => {
      if (ev.key === "Enter") { ev.preventDefault(); finish(true); }
      if (ev.key === "Escape") { ev.preventDefault(); finish(false); }
    };
    input.onblur = () => finish(true);
  }

  /* ================= 工具栏状态 ================= */

  setTool(tool) { this.tool = tool; }

  setStyle({ stroke, fill, fillEnabled, strokeWidth }) {
    if (stroke !== undefined) this.strokeColor = stroke;
    if (fill !== undefined) this.fillColor = fill;
    if (fillEnabled !== undefined) this.fillEnabled = fillEnabled;
    if (strokeWidth !== undefined) this.strokeWidth = strokeWidth;
  }
}

/** 用新对象替换 map 中同 id 的对象（保持插入顺序）。 */
function shapesReplace(map, oldS, newS) {
  const arr = [...map.entries()];
  map.clear();
  for (const [k, v] of arr) {
    if (v === oldS) map.set(k, newS);
    else map.set(k, v);
  }
}

export { drawShape, measureTextWidth };
