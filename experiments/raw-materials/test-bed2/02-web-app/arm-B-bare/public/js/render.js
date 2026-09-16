/**
 * render.js — 画布渲染：世界坐标 ↔ 屏幕坐标变换、按需重绘循环、
 * 远端光标层管理。
 */
import { WORLD_W, WORLD_H, drawShapes } from "./shapes.js";

export class Renderer {
  /**
   * @param {HTMLCanvasElement} canvas
   * @param {HTMLDivElement} cursorLayer
   */
  constructor(canvas, cursorLayer) {
    this.canvas = canvas;
    this.cursorLayer = cursorLayer;
    this.ctx = canvas.getContext("2d");
    this.scale = 1;
    this.offsetX = 0;
    this.offsetY = 0;

    this.shapes = new Map();          // 由 editor 维护写入
    this.selectedId = null;           // 由 editor 维护
    /** @type {Map<string, object>} uid -> draft shape */
    this.drafts = new Map();

    this._dirty = true;
    this._cursors = new Map();        // uid -> {x, y, name, color, el}
    this._loop = this._loop.bind(this);
    requestAnimationFrame(this._loop);
  }

  /** 依据容器尺寸重算变换（窗口 resize 时调用）。 */
  resize() {
    const wrap = this.canvas.parentElement;
    const dpr = window.devicePixelRatio || 1;
    const cssW = wrap.clientWidth;
    const cssH = wrap.clientHeight;
    this.canvas.width = Math.round(cssW * dpr);
    this.canvas.height = Math.round(cssH * dpr);

    // 世界 → 屏幕：等比缩放并居中（letterbox）
    const scale = Math.min(cssW / WORLD_W, cssH / WORLD_H) * 0.98;
    this.scale = scale * dpr;
    this.offsetX = (cssW * dpr - WORLD_W * this.scale) / 2;
    this.offsetY = (cssH * dpr - WORLD_H * this.scale) / 2;

    // cursorLayer 用 CSS 像素坐标，单独保存一份换算
    this.cssScale = scale;
    this.cssOffsetX = (cssW - WORLD_W * scale) / 2;
    this.cssOffsetY = (cssH - WORLD_H * scale) / 2;

    this.invalidate();
  }

  /** 屏幕事件坐标 → 世界坐标。 */
  toWorld(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    const cx = clientX - rect.left;
    const cy = clientY - rect.top;
    return {
      x: (cx - this.cssOffsetX) / this.cssScale,
      y: (cy - this.cssOffsetY) / this.cssScale,
    };
  }

  /** 世界坐标 → cursorLayer 的 CSS 像素坐标。 */
  worldToCss(x, y) {
    return {
      x: x * this.cssScale + this.cssOffsetX,
      y: y * this.cssScale + this.cssOffsetY,
    };
  }

  invalidate() { this._dirty = true; }

  _loop() {
    if (this._dirty) {
      this._dirty = false;
      this._draw();
    }
    requestAnimationFrame(this._loop);
  }

  _draw() {
    const { ctx, canvas } = this;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 白板底 + 画布区域
    ctx.fillStyle = "#f8f9fb";
    ctx.fillRect(
      this.offsetX, this.offsetY,
      WORLD_W * this.scale, WORLD_H * this.scale
    );
    ctx.strokeStyle = "#c8cdd6";
    ctx.lineWidth = 1;
    ctx.strokeRect(
      this.offsetX, this.offsetY,
      WORLD_W * this.scale, WORLD_H * this.scale
    );

    ctx.setTransform(this.scale, 0, 0, this.scale, this.offsetX, this.offsetY);
    drawShapes(ctx, this.shapes, {
      selected: (id) => id === this.selectedId,
      drafts: this._draftsWithMine(),
    });
    ctx.setTransform(1, 0, 0, 1, 0, 0);
  }

  _draftsWithMine() {
    // drawShapes 期望 drafts: Map(uid -> shape|null)
    return this.drafts;
  }

  /* ---------- 远端光标 ---------- */

  updateCursor(uid, name, color, wx, wy) {
    let cur = this._cursors.get(uid);
    if (!cur) {
      const el = document.createElement("div");
      el.className = "remote-cursor";
      el.innerHTML = `<div class="dot"></div><div class="label"></div>`;
      this.cursorLayer.appendChild(el);
      cur = { el, dot: el.querySelector(".dot"), label: el.querySelector(".label") };
      this._cursors.set(uid, cur);
    }
    cur.dot.style.background = color;
    cur.label.textContent = name;
    cur.label.style.background = color;
    const p = this.worldToCss(wx, wy);
    cur.el.style.left = `${p.x}px`;
    cur.el.style.top = `${p.y}px`;
  }

  removeCursor(uid) {
    const cur = this._cursors.get(uid);
    if (cur) {
      cur.el.remove();
      this._cursors.delete(uid);
    }
  }

  clearCursors() {
    for (const uid of [...this._cursors.keys()]) this.removeCursor(uid);
  }

  /** 导出 PNG：按世界坐标离屏重绘。 */
  exportPng() {
    const off = document.createElement("canvas");
    off.width = WORLD_W;
    off.height = WORLD_H;
    const ctx = off.getContext("2d");
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, WORLD_W, WORLD_H);
    drawShapes(ctx, this.shapes, { drafts: new Map() });
    return off.toDataURL("image/png");
  }
}
