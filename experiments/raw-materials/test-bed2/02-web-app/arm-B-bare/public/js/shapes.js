/**
 * shapes.js — 图形模型、几何计算与 Canvas 绘制。
 *
 * 世界坐标系固定为 WORLD_W × WORLD_H，各客户端等比缩放适配自己的画布，
 * 因此不同窗口大小的用户看到的白板内容完全对齐。
 */

export const WORLD_W = 1600;
export const WORLD_H = 1000;

export const TYPES = ["rect", "ellipse", "arrow", "text"];

/** 依据两个对角点构造图形对象。 */
export function makeShape(type, id, x1, y1, x2, y2, opts = {}) {
  return {
    id,
    type,
    x1, y1, x2, y2,
    stroke: opts.stroke || "#1e88e5",
    fill: opts.fill ?? null,
    strokeWidth: opts.strokeWidth ?? 2,
    text: opts.text ?? "",
    fontSize: opts.fontSize ?? 28,
    createdBy: opts.createdBy ?? "",
  };
}

export function boundsOf(s) {
  return {
    x: Math.min(s.x1, s.x2),
    y: Math.min(s.y1, s.y2),
    w: Math.abs(s.x2 - s.x1),
    h: Math.abs(s.y2 - s.y1),
  };
}

/** 平移图形（拖动用）。 */
export function translateShape(s, dx, dy) {
  s.x1 += dx; s.y1 += dy; s.x2 += dx; s.y2 += dy;
}

/** 命中测试：世界坐标点是否落在图形上（含 4px 容差）。 */
export function hitTest(s, px, py) {
  const tol = Math.max(6, s.strokeWidth + 4);
  const b = boundsOf(s);
  if (s.type === "rect") {
    return px >= b.x - tol && px <= b.x + b.w + tol &&
           py >= b.y - tol && py <= b.y + b.h + tol;
  }
  if (s.type === "ellipse") {
    const cx = b.x + b.w / 2, cy = b.y + b.h / 2;
    const rx = b.w / 2 + tol, ry = b.h / 2 + tol;
    if (rx <= 0 || ry <= 0) return false;
    const nx = (px - cx) / rx, ny = (py - cy) / ry;
    return nx * nx + ny * ny <= 1;
  }
  if (s.type === "text") {
    const w = Math.max(b.w, measureTextWidth(s));
    const h = Math.max(b.h, s.fontSize * 1.3);
    return px >= b.x - tol && px <= b.x + w + tol &&
           py >= b.y - tol && py <= b.y + h + tol;
  }
  if (s.type === "arrow") {
    return distToSegment(px, py, s.x1, s.y1, s.x2, s.y2) <= tol;
  }
  return false;
}

/** 从后往前（最上层优先）找出被点中的图形 id。 */
export function pickShape(shapes, px, py) {
  const list = [...shapes.values()];
  for (let i = list.length - 1; i >= 0; i--) {
    if (hitTest(list[i], px, py)) return list[i].id;
  }
  return null;
}

function distToSegment(px, py, x1, y1, x2, y2) {
  const dx = x2 - x1, dy = y2 - y1;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return Math.hypot(px - x1, py - y1);
  let t = ((px - x1) * dx + (py - y1) * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
}

let _measureCtx = null;
export function measureTextWidth(s) {
  if (!_measureCtx) _measureCtx = document.createElement("canvas").getContext("2d");
  _measureCtx.font = `${s.fontSize}px "Segoe UI", "Microsoft YaHei", sans-serif`;
  return _measureCtx.measureText(s.text || "").width;
}

/* ---------------- 绘制 ---------------- */

/** 把一组图形绘制到指定 2D 上下文（ctx 已按世界变换设置好）。
 *  opts.selected 可为 id 或谓词函数；opts.drafts: Map(uid -> shape|null)。 */
export function drawShapes(ctx, shapes, opts = {}) {
  const selectedFn = typeof opts.selected === "function"
    ? opts.selected
    : (id) => id === opts.selected;
  for (const s of shapes.values()) {
    drawShape(ctx, s, { ...opts, selected: selectedFn(s.id) });
  }
  // 远端正在绘制中的预览：以对方颜色高亮描出
  for (const draft of (opts.drafts && opts.drafts.values()) || []) {
    if (draft) drawShape(ctx, draft, { draftColor: draft.stroke || "#999" });
  }
}

export function drawShape(ctx, s, opts = {}) {
  const stroke = opts.draftColor || s.stroke;
  const b = boundsOf(s);
  ctx.lineWidth = s.strokeWidth;
  ctx.strokeStyle = stroke;
  ctx.fillStyle = s.fill || "transparent";
  ctx.setLineDash([]);

  switch (s.type) {
    case "rect": {
      ctx.beginPath();
      ctx.rect(b.x, b.y, b.w, b.h);
      if (s.fill) ctx.fill();
      ctx.stroke();
      break;
    }
    case "ellipse": {
      ctx.beginPath();
      ctx.ellipse(b.x + b.w / 2, b.y + b.h / 2, b.w / 2, b.h / 2, 0, 0, Math.PI * 2);
      if (s.fill) ctx.fill();
      ctx.stroke();
      break;
    }
    case "arrow": {
      drawArrow(ctx, s.x1, s.y1, s.x2, s.y2, Math.max(10, s.strokeWidth * 4));
      break;
    }
    case "text": {
      ctx.fillStyle = s.stroke;
      ctx.font = `${s.fontSize}px "Segoe UI", "Microsoft YaHei", sans-serif`;
      ctx.textBaseline = "top";
      const lines = String(s.text || "").split("\n");
      lines.forEach((line, i) => {
        ctx.fillText(line, s.x1, s.y1 + i * s.fontSize * 1.3);
      });
      break;
    }
  }

  if (opts.selected) {
    drawSelectionBox(ctx, s);
  }
}

function drawArrow(ctx, x1, y1, x2, y2, headLen) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - headLen * Math.cos(angle - Math.PI / 7), y2 - headLen * Math.sin(angle - Math.PI / 7));
  ctx.lineTo(x2 - headLen * Math.cos(angle + Math.PI / 7), y2 - headLen * Math.sin(angle + Math.PI / 7));
  ctx.closePath();
  ctx.fillStyle = ctx.strokeStyle;
  ctx.fill();
}

function drawSelectionBox(ctx, s) {
  const pad = 6;
  let x, y, w, h;
  if (s.type === "arrow") {
    x = Math.min(s.x1, s.x2) - pad;
    y = Math.min(s.y1, s.y2) - pad;
    w = Math.abs(s.x2 - s.x1) + pad * 2;
    h = Math.abs(s.y2 - s.y1) + pad * 2;
  } else if (s.type === "text") {
    x = s.x1 - pad;
    y = s.y1 - pad;
    w = Math.max(40, measureTextWidth(s)) + pad * 2;
    h = String(s.text || "").split("\n").length * s.fontSize * 1.3 + pad * 2;
  } else {
    const b = boundsOf(s);
    x = b.x - pad; y = b.y - pad;
    w = b.w + pad * 2; h = b.h + pad * 2;
  }
  ctx.save();
  ctx.strokeStyle = "#4f8cff";
  ctx.lineWidth = 1.5;
  ctx.setLineDash([6, 4]);
  ctx.strokeRect(x, y, w, h);
  ctx.restore();
}
