/* 协作白板前端逻辑 */
(() => {
  'use strict';

  // ===== 常量 =====
  const BOARD_W = 2000;          // 虚拟画板宽（所有用户共享同一坐标系）
  const BOARD_H = 1200;          // 虚拟画板高
  const CURSOR_TTL = 4000;       // 远程光标超时（毫秒）
  const UNDO_LIMIT = 100;
  const FONT_STACK = 'system-ui, -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif';
  const PALETTE = ['#1e293b', '#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#3b82f6', '#a855f7', '#ec4899'];

  // ===== DOM =====
  const canvas = document.getElementById('board');
  const ctx = canvas.getContext('2d');
  const wrap = document.getElementById('canvas-wrap');
  const editor = document.getElementById('text-editor');
  const toastEl = document.getElementById('toast');
  const onlineEl = document.getElementById('online');
  const onlineCountEl = document.getElementById('online-count');
  const connEl = document.getElementById('conn');
  const statusDotEl = document.getElementById('status-dot');
  const statusTextEl = document.getElementById('status-text');
  const btnUndo = document.getElementById('btn-undo');
  const btnRedo = document.getElementById('btn-redo');
  const btnClear = document.getElementById('btn-clear');
  const btnShare = document.getElementById('btn-share');
  const swatchWrap = document.getElementById('swatches');
  const customColor = document.getElementById('custom-color');
  const strokeRange = document.getElementById('stroke-width');
  const strokeVal = document.getElementById('stroke-val');
  const fontSizeSel = document.getElementById('font-size');

  // ===== 状态 =====
  const shapes = new Map();          // id -> shape
  const users = new Map();           // id -> {id,name,color}
  const remoteCursors = new Map();   // id -> {x,y,name,color,ts}
  const undoStack = [];
  const redoStack = [];

  let selfId = null;
  let roomId = null;
  let tool = 'select';
  let drawColor = '#1e293b';
  let strokeWidth = 3;
  let fontSize = 28;
  let draft = null;                  // 正在绘制的形状
  let dragInfo = null;               // 正在拖动移动的形状信息
  let selectedId = null;
  let textEditing = null;            // {id|null, x, y}
  let ws = null;
  let reconnectDelay = 500;

  // ===== 视图变换：虚拟坐标 <-> 屏幕 =====
  let dpr = 1, scale = 1, offX = 0, offY = 0;

  function resizeCanvas() {
    dpr = window.devicePixelRatio || 1;
    const cssW = wrap.clientWidth, cssH = wrap.clientHeight;
    canvas.width = Math.max(1, Math.round(cssW * dpr));
    canvas.height = Math.max(1, Math.round(cssH * dpr));
    canvas.style.width = cssW + 'px';
    canvas.style.height = cssH + 'px';
    scale = Math.min(cssW / BOARD_W, cssH / BOARD_H) * 0.98;
    offX = (cssW - BOARD_W * scale) / 2;
    offY = (cssH - BOARD_H * scale) / 2;
    requestRender();
  }

  function toBoard(px, py) {
    return { x: (px - offX) / scale, y: (py - offY) / scale };
  }

  // ===== 渲染 =====
  let renderQueued = false;
  function requestRender() {
    if (renderQueued) return;
    renderQueued = true;
    requestAnimationFrame(() => { renderQueued = false; render(); });
  }

  function render() {
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

    // 画板外区域
    ctx.fillStyle = '#eef2f7';
    ctx.fillRect(0, 0, canvas.width / dpr, canvas.height / dpr);

    ctx.save();
    ctx.translate(offX, offY);
    ctx.scale(scale, scale);

    // 画板底板
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, BOARD_W, BOARD_H);
    ctx.strokeStyle = '#cbd5e1';
    ctx.lineWidth = 1 / scale;
    ctx.strokeRect(0, 0, BOARD_W, BOARD_H);

    // 网格点
    ctx.fillStyle = '#dde5ee';
    for (let gx = 50; gx < BOARD_W; gx += 50) {
      for (let gy = 50; gy < BOARD_H; gy += 50) {
        ctx.fillRect(gx - 1, gy - 1, 2, 2);
      }
    }

    // 已提交的形状
    for (const s of shapes.values()) drawShape(s);

    // 正在绘制的形状
    if (draft) drawShape(draft);

    // 选中框
    if (selectedId) {
      const s = shapes.get(selectedId);
      if (s) {
        const b = shapeBBox(s);
        ctx.save();
        ctx.strokeStyle = '#4f46e5';
        ctx.lineWidth = 1.5 / scale;
        ctx.setLineDash([8, 6]);
        ctx.strokeRect(b.x - 8, b.y - 8, b.w + 16, b.h + 16);
        ctx.restore();
      }
    }
    ctx.restore();

    // 远程光标（屏幕坐标系）
    renderCursors();
  }

  function drawShape(s) {
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.strokeStyle = s.color;
    ctx.fillStyle = s.color;
    ctx.lineWidth = s.width;

    if (s.type === 'rect') {
      ctx.strokeRect(s.x, s.y, s.w, s.h);
    } else if (s.type === 'ellipse') {
      ctx.beginPath();
      ctx.ellipse(s.x + s.w / 2, s.y + s.h / 2, Math.abs(s.w) / 2, Math.abs(s.h) / 2, 0, 0, Math.PI * 2);
      ctx.stroke();
    } else if (s.type === 'arrow') {
      const ang = Math.atan2(s.y2 - s.y1, s.x2 - s.x1);
      const head = Math.max(14, s.width * 4);
      ctx.beginPath();
      ctx.moveTo(s.x1, s.y1);
      ctx.lineTo(s.x2, s.y2);
      ctx.moveTo(s.x2, s.y2);
      ctx.lineTo(s.x2 - head * Math.cos(ang - Math.PI / 7), s.y2 - head * Math.sin(ang - Math.PI / 7));
      ctx.moveTo(s.x2, s.y2);
      ctx.lineTo(s.x2 - head * Math.cos(ang + Math.PI / 7), s.y2 - head * Math.sin(ang + Math.PI / 7));
      ctx.stroke();
    } else if (s.type === 'pencil') {
      if (s.points.length === 1) {
        ctx.beginPath();
        ctx.arc(s.points[0][0], s.points[0][1], s.width / 2, 0, Math.PI * 2);
        ctx.fill();
        return;
      }
      ctx.beginPath();
      ctx.moveTo(s.points[0][0], s.points[0][1]);
      for (let i = 1; i < s.points.length; i++) ctx.lineTo(s.points[i][0], s.points[i][1]);
      ctx.stroke();
    } else if (s.type === 'text') {
      ctx.font = s.size + 'px ' + FONT_STACK;
      ctx.textBaseline = 'top';
      const lines = String(s.text).split('\n');
      for (let i = 0; i < lines.length; i++) {
        ctx.fillText(lines[i], s.x, s.y + i * s.size * 1.35);
      }
    }
  }

  function renderCursors() {
    const now = Date.now();
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    for (const [id, c] of remoteCursors) {
      if (now - c.ts > CURSOR_TTL) { remoteCursors.delete(id); continue; }
      const sx = offX + c.x * scale, sy = offY + c.y * scale;
      ctx.fillStyle = c.color;
      ctx.beginPath();
      ctx.moveTo(sx, sy);
      ctx.lineTo(sx + 11, sy + 4.5);
      ctx.lineTo(sx + 4.5, sy + 11);
      ctx.closePath();
      ctx.fill();
      ctx.font = '12px ' + FONT_STACK;
      const tw = ctx.measureText(c.name).width;
      ctx.fillRect(sx + 13, sy + 13, tw + 12, 19);
      ctx.fillStyle = '#ffffff';
      ctx.textBaseline = 'middle';
      ctx.fillText(c.name, sx + 19, sy + 23);
    }
  }

  // 定时清理过期光标
  setInterval(() => { if (remoteCursors.size) requestRender(); }, 1500);

  // ===== 几何辅助 =====
  const measureCtx = document.createElement('canvas').getContext('2d');

  function measureText(text, size) {
    measureCtx.font = size + 'px ' + FONT_STACK;
    const lines = String(text).split('\n');
    let w = 0;
    for (const ln of lines) w = Math.max(w, measureCtx.measureText(ln).width);
    return { w, h: lines.length * size * 1.35 };
  }

  function shapeBBox(s) {
    if (s.type === 'rect' || s.type === 'ellipse') {
      return { x: Math.min(s.x, s.x + s.w), y: Math.min(s.y, s.y + s.h), w: Math.abs(s.w), h: Math.abs(s.h) };
    }
    if (s.type === 'arrow') {
      const x = Math.min(s.x1, s.x2), y = Math.min(s.y1, s.y2);
      return { x, y, w: Math.abs(s.x2 - s.x1), h: Math.abs(s.y2 - s.y1) };
    }
    if (s.type === 'text') {
      return { x: s.x, y: s.y, w: s.w || s.size * 2, h: s.h || s.size * 1.35 };
    }
    if (s.type === 'pencil') {
      let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
      for (const [px, py] of s.points) {
        if (px < minX) minX = px;
        if (py < minY) minY = py;
        if (px > maxX) maxX = px;
        if (py > maxY) maxY = py;
      }
      return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
    }
    return { x: 0, y: 0, w: 0, h: 0 };
  }

  function distToSeg(px, py, x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1;
    const len2 = dx * dx + dy * dy;
    if (len2 === 0) return Math.hypot(px - x1, py - y1);
    let t = ((px - x1) * dx + (py - y1) * dy) / len2;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(px - (x1 + t * dx), py - (y1 + t * dy));
  }

  function hitShape(s, p) {
    const tol = Math.max(10, (s.width || 3) + 7);
    const b = shapeBBox(s);
    if (p.x < b.x - tol || p.x > b.x + b.w + tol || p.y < b.y - tol || p.y > b.y + b.h + tol) return false;
    if (s.type === 'rect' || s.type === 'ellipse' || s.type === 'text') return true;
    if (s.type === 'arrow') return distToSeg(p.x, p.y, s.x1, s.y1, s.x2, s.y2) <= tol;
    if (s.type === 'pencil') {
      if (s.points.length === 1) return Math.hypot(p.x - s.points[0][0], p.y - s.points[0][1]) <= tol;
      for (let i = 1; i < s.points.length; i++) {
        if (distToSeg(p.x, p.y, s.points[i - 1][0], s.points[i - 1][1], s.points[i][0], s.points[i][1]) <= tol) return true;
      }
      return false;
    }
    return false;
  }

  function hitTest(p) {
    const arr = [...shapes.values()];
    for (let i = arr.length - 1; i >= 0; i--) {
      if (hitShape(arr[i], p)) return arr[i];
    }
    return null;
  }

  // ===== 工具切换 =====
  function setTool(t) {
    commitTextEditor();
    tool = t;
    draft = null;
    selectedId = null;
    document.querySelectorAll('[data-tool]').forEach((b) => b.classList.toggle('active', b.dataset.tool === t));
    canvas.style.cursor = t === 'select' ? 'default' : (t === 'text' ? 'text' : 'crosshair');
    requestRender();
  }

  document.querySelectorAll('[data-tool]').forEach((btn) => {
    btn.addEventListener('click', () => setTool(btn.dataset.tool));
  });

  // ===== 颜色 / 粗细 / 字号 =====
  PALETTE.forEach((c, i) => {
    const b = document.createElement('button');
    b.className = 'swatch' + (i === 0 ? ' active' : '');
    b.style.background = c;
    b.title = c;
    b.addEventListener('click', () => {
      drawColor = c;
      markSwatch(b);
    });
    swatchWrap.appendChild(b);
  });
  function markSwatch(activeEl) {
    document.querySelectorAll('.swatch').forEach((el) => el.classList.toggle('active', el === activeEl));
  }
  customColor.addEventListener('input', () => {
    drawColor = customColor.value;
    markSwatch(null);
  });
  strokeRange.addEventListener('input', () => {
    strokeWidth = Number(strokeRange.value);
    strokeVal.textContent = strokeRange.value;
  });
  fontSizeSel.addEventListener('change', () => {
    fontSize = Number(fontSizeSel.value);
  });

  // ===== 撤销 / 重做 =====
  // 操作记录：
  //  {kind:'add', shape}                添加
  //  {kind:'delete', shape}             删除
  //  {kind:'update', id, before, after} 修改（移动/文字编辑，形状快照）
  //  {kind:'clear', before:[...]}       清空（保存清空前的全部形状）
  function snapshot(s) { return JSON.parse(JSON.stringify(s)); }

  function pushUndo(op) {
    undoStack.push(op);
    if (undoStack.length > UNDO_LIMIT) undoStack.shift();
    redoStack.length = 0;
    syncUndoButtons();
  }
  function syncUndoButtons() {
    btnUndo.disabled = undoStack.length === 0;
    btnRedo.disabled = redoStack.length === 0;
  }

  function applyOp(op) {  // 正向执行（重做时用）
    if (op.kind === 'add') {
      shapes.set(op.shape.id, snapshot(op.shape));
      send({ type: 'add', shape: op.shape });
    } else if (op.kind === 'delete') {
      shapes.delete(op.shape.id);
      if (selectedId === op.shape.id) selectedId = null;
      send({ type: 'delete', id: op.shape.id });
    } else if (op.kind === 'update') {
      const s = shapes.get(op.id);
      if (!s) return;
      Object.assign(s, snapshot(op.after));
      send({ type: 'update', shape: snapshot(s) });
    } else if (op.kind === 'clear') {
      shapes.clear();
      selectedId = null;
      send({ type: 'clear' });
    }
    requestRender();
  }

  function applyInverse(op) {  // 逆向执行（撤销时用）
    if (op.kind === 'add') {
      applyOp({ kind: 'delete', shape: op.shape });
    } else if (op.kind === 'delete') {
      applyOp({ kind: 'add', shape: op.shape });
    } else if (op.kind === 'update') {
      applyOp({ kind: 'update', id: op.id, before: op.after, after: op.before });
    } else if (op.kind === 'clear') {
      for (const s of op.before) {
        shapes.set(s.id, snapshot(s));
        send({ type: 'add', shape: s });
      }
      requestRender();
    }
  }

  function doUndo() {
    const op = undoStack.pop();
    if (!op) return;
    applyInverse(op);
    redoStack.push(op);
    syncUndoButtons();
  }
  function doRedo() {
    const op = redoStack.pop();
    if (!op) return;
    applyOp(op);
    undoStack.push(op);
    syncUndoButtons();
  }
  btnUndo.addEventListener('click', doUndo);
  btnRedo.addEventListener('click', doRedo);

  function deleteSelected() {
    const s = shapes.get(selectedId);
    if (!s) return;
    shapes.delete(s.id);
    send({ type: 'delete', id: s.id });
    pushUndo({ kind: 'delete', shape: snapshot(s) });
    selectedId = null;
    requestRender();
  }

  btnClear.addEventListener('click', () => {
    if (shapes.size === 0) return;
    if (!confirm('确定清空整个画板？所有人都会看到画板被清空（可用 Ctrl+Z 撤销）。')) return;
    const before = [...shapes.values()].map(snapshot);
    shapes.clear();
    selectedId = null;
    send({ type: 'clear' });
    pushUndo({ kind: 'clear', before });
    requestRender();
  });

  // ===== 绘制 =====
  function genId() {
    const a = new Uint8Array(8);
    crypto.getRandomValues(a);
    return Array.from(a, (b) => b.toString(16).padStart(2, '0')).join('');
  }

  function makeDraft(p) {
    const base = { id: genId(), color: drawColor, width: strokeWidth };
    if (tool === 'rect' || tool === 'ellipse') return Object.assign(base, { type: tool, x: p.x, y: p.y, w: 0, h: 0 });
    if (tool === 'arrow') return Object.assign(base, { type: 'arrow', x1: p.x, y1: p.y, x2: p.x, y2: p.y });
    if (tool === 'pencil') return Object.assign(base, { type: 'pencil', points: [[p.x, p.y]] });
    return null;
  }

  function updateDraft(p, shift) {
    if (tool === 'rect' || tool === 'ellipse') {
      let w = p.x - draft.x, h = p.y - draft.y;
      if (shift) {
        const m = Math.max(Math.abs(w), Math.abs(h));
        w = (w < 0 ? -1 : 1) * m;
        h = (h < 0 ? -1 : 1) * m;
      }
      draft.w = w; draft.h = h;
    } else if (tool === 'arrow') {
      if (shift) {
        const dx = p.x - draft.x1, dy = p.y - draft.y1;
        const snap = Math.PI / 4;
        const ang = Math.round(Math.atan2(dy, dx) / snap) * snap;
        const len = Math.hypot(dx, dy);
        draft.x2 = draft.x1 + Math.cos(ang) * len;
        draft.y2 = draft.y1 + Math.sin(ang) * len;
      } else {
        draft.x2 = p.x; draft.y2 = p.y;
      }
    } else if (tool === 'pencil') {
      const pts = draft.points;
      const last = pts[pts.length - 1];
      if (Math.hypot(p.x - last[0], p.y - last[1]) > 3) pts.push([p.x, p.y]);
    }
  }

  function shapeSignificant(s) {
    if (s.type === 'rect' || s.type === 'ellipse') return Math.abs(s.w) > 4 && Math.abs(s.h) > 4;
    if (s.type === 'arrow') return Math.hypot(s.x2 - s.x1, s.y2 - s.y1) > 6;
    if (s.type === 'pencil') return s.points.length > 1;
    return false;
  }

  function normalizeRectLike(s) {
    if (s.w < 0) { s.x += s.w; s.w = -s.w; }
    if (s.h < 0) { s.y += s.h; s.h = -s.h; }
  }

  function applyMove(s, orig, dx, dy) {
    if (s.type === 'rect' || s.type === 'ellipse' || s.type === 'text') {
      s.x = orig.x + dx; s.y = orig.y + dy;
    } else if (s.type === 'arrow') {
      s.x1 = orig.x1 + dx; s.y1 = orig.y1 + dy;
      s.x2 = orig.x2 + dx; s.y2 = orig.y2 + dy;
    } else if (s.type === 'pencil') {
      s.points = orig.points.map(([px, py]) => [px + dx, py + dy]);
    }
  }

  // ===== 指针事件 =====
  let lastCursorSent = 0;

  function eventBoardPos(e) {
    const rect = canvas.getBoundingClientRect();
    return toBoard(e.clientX - rect.left, e.clientY - rect.top);
  }

  canvas.addEventListener('pointerdown', (e) => {
    if (e.button !== 0) return;
    commitTextEditor();
    const p = eventBoardPos(e);
    try { canvas.setPointerCapture(e.pointerId); } catch (err) { /* 合成事件等场景忽略 */ }

    if (tool === 'select') {
      const hit = hitTest(p);
      selectedId = hit ? hit.id : null;
      if (hit) {
        dragInfo = { id: hit.id, orig: snapshot(hit), startBoard: p, lastSent: 0, moved: false };
      }
      requestRender();
    } else if (tool === 'text') {
      openTextEditor(null, p, null);
    } else {
      draft = makeDraft(p);
      requestRender();
    }
  });

  canvas.addEventListener('pointermove', (e) => {
    const p = eventBoardPos(e);
    const now = performance.now();
    if (now - lastCursorSent > 40) {
      lastCursorSent = now;
      send({ type: 'cursor', x: p.x, y: p.y });
    }
    if (draft) {
      updateDraft(p, e.shiftKey);
      requestRender();
    } else if (dragInfo) {
      const s = shapes.get(dragInfo.id);
      if (!s) { dragInfo = null; return; }
      const dx = p.x - dragInfo.startBoard.x, dy = p.y - dragInfo.startBoard.y;
      if (dx !== 0 || dy !== 0) dragInfo.moved = true;
      applyMove(s, dragInfo.orig, dx, dy);
      if (now - dragInfo.lastSent > 50) {
        dragInfo.lastSent = now;
        send({ type: 'update', shape: snapshot(s) });
      }
      requestRender();
    }
  });

  function finishPointer() {
    if (draft) {
      const s = draft;
      draft = null;
      if (shapeSignificant(s)) {
        if (s.type === 'rect' || s.type === 'ellipse') normalizeRectLike(s);
        shapes.set(s.id, s);
        send({ type: 'add', shape: s });
        pushUndo({ kind: 'add', shape: snapshot(s) });
        selectedId = s.id;
      }
      requestRender();
    } else if (dragInfo) {
      const s = shapes.get(dragInfo.id);
      if (s && dragInfo.moved) {
        send({ type: 'update', shape: snapshot(s) });
        pushUndo({ kind: 'update', id: s.id, before: dragInfo.orig, after: snapshot(s) });
      }
      dragInfo = null;
      requestRender();
    }
  }
  canvas.addEventListener('pointerup', finishPointer);
  canvas.addEventListener('pointercancel', () => { draft = null; dragInfo = null; requestRender(); });

  canvas.addEventListener('dblclick', (e) => {
    if (tool !== 'select') return;
    const p = eventBoardPos(e);
    const hit = hitTest(p);
    if (hit && hit.type === 'text') openTextEditor(hit.id, { x: hit.x, y: hit.y }, hit);
  });

  // ===== 文字编辑器 =====
  function openTextEditor(shapeId, boardPos, existing) {
    textEditing = { id: shapeId, x: boardPos.x, y: boardPos.y };
    editor.value = existing ? existing.text : '';
    editor.style.color = existing ? existing.color : drawColor;
    const fs = existing ? existing.size : fontSize;
    editor.style.fontSize = (fs * scale) + 'px';
    editor.style.left = (offX + boardPos.x * scale) + 'px';
    editor.style.top = (offY + boardPos.y * scale) + 'px';
    editor.style.width = Math.max(80, 400 * scale) + 'px';
    editor.style.height = 'auto';
    editor.rows = 1;
    editor.hidden = false;
    editor.focus();
    editor.selectionStart = editor.value.length;
  }

  function autoGrowEditor() {
    editor.style.height = 'auto';
    editor.style.height = (editor.scrollHeight + 2) + 'px';
  }
  editor.addEventListener('input', autoGrowEditor);

  function commitTextEditor() {
    if (!textEditing) return;
    const info = textEditing;
    textEditing = null;
    editor.hidden = true;
    const val = editor.value.replace(/\s+$/, '');
    if (!val.trim()) return; // 空内容视为取消

    if (info.id) {
      const s = shapes.get(info.id);
      if (!s) return;
      const before = snapshot(s);
      s.text = val;
      const m = measureText(val, s.size);
      s.w = m.w; s.h = m.h;
      send({ type: 'update', shape: snapshot(s) });
      pushUndo({ kind: 'update', id: s.id, before, after: snapshot(s) });
    } else {
      const m = measureText(val, fontSize);
      const s = {
        id: genId(), type: 'text',
        x: info.x, y: info.y, text: val,
        size: fontSize, color: drawColor,
        w: m.w, h: m.h,
      };
      shapes.set(s.id, s);
      send({ type: 'add', shape: s });
      pushUndo({ kind: 'add', shape: snapshot(s) });
      selectedId = s.id;
    }
    requestRender();
  }

  editor.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      commitTextEditor();
    } else if (e.key === 'Escape') {
      textEditing = null;   // 先清标志，随后的 blur 不会再提交
      editor.hidden = true;
    }
  });
  editor.addEventListener('blur', () => {
    // Escape 已把 textEditing 置空，这里只会提交正常路径
    setTimeout(() => { if (textEditing && !editor.hidden) commitTextEditor(); }, 0);
  });

  // ===== 键盘快捷键 =====
  window.addEventListener('keydown', (e) => {
    const tag = ((e.target && e.target.tagName) || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select') return;

    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key.toLowerCase() === 'z') {
      e.preventDefault(); doUndo(); return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key.toLowerCase() === 'y' || (e.shiftKey && e.key.toLowerCase() === 'z'))) {
      e.preventDefault(); doRedo(); return;
    }
    if (e.key === 'Delete' || e.key === 'Backspace') {
      if (selectedId) { e.preventDefault(); deleteSelected(); }
      return;
    }
    if (e.key === 'Escape') {
      draft = null;
      selectedId = null;
      requestRender();
      return;
    }
    if (!e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1) {
      const map = { v: 'select', r: 'rect', c: 'ellipse', a: 'arrow', t: 'text', p: 'pencil' };
      const t = map[e.key.toLowerCase()];
      if (t) setTool(t);
    }
  });

  // ===== 分享 =====
  btnShare.addEventListener('click', async () => {
    const url = location.href;
    try {
      await navigator.clipboard.writeText(url);
      toast('分享链接已复制：' + url);
    } catch (err) {
      prompt('复制此链接分享给其他人：', url);
    }
  });

  // ===== 提示气泡 =====
  let toastTimer = null;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.hidden = false;
    requestAnimationFrame(() => toastEl.classList.add('show'));
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toastEl.classList.remove('show');
      setTimeout(() => { toastEl.hidden = true; }, 300);
    }, 2400);
  }

  // ===== 在线用户 =====
  function renderUsers() {
    onlineCountEl.textContent = String(users.size);
    const names = [...users.values()].map((u) => u.name + (u.id === selfId ? '（你）' : '')).join('、');
    onlineEl.title = names || '';
  }

  // ===== WebSocket 通信 =====
  function setStatus(cls, text) {
    connEl.className = 'conn ' + cls;
    statusTextEl.textContent = text;
  }

  function wsUrl() {
    const proto = location.protocol === 'https:' ? 'wss://' : 'ws://';
    return proto + location.host + '/ws';
  }

  const sendLog = [];
  function send(obj) {
    if (ws && ws.readyState === WebSocket.OPEN) {
      try {
        ws.send(JSON.stringify(obj));
        sendLog.push({ t: Date.now(), type: obj.type });
        if (sendLog.length > 100) sendLog.shift();
      } catch (e) { /* ignore */ }
    }
  }

  function connect() {
    setStatus('', '连接中…');
    try {
      ws = new WebSocket(wsUrl());
    } catch (e) {
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      reconnectDelay = 500;
      setStatus('online', '已连接');
      send({ type: 'join', room: roomId });
    };
    ws.onmessage = (ev) => {
      let m;
      try { m = JSON.parse(ev.data); } catch (e) { return; }
      if (m && typeof m === 'object') handleServer(m);
    };
    ws.onclose = () => {
      setStatus('offline', '连接断开，重连中…');
      scheduleReconnect();
    };
    ws.onerror = () => { try { ws.close(); } catch (e) { /* ignore */ } };
  }

  function scheduleReconnect() {
    setTimeout(connect, reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 2, 8000);
  }

  const recvErrors = [];
  function handleServer(m) {
    switch (m.type) {
      case 'init': {
        selfId = m.selfId;
        shapes.clear();
        for (const s of m.shapes || []) shapes.set(s.id, s);
        users.clear();
        for (const u of m.users || []) users.set(u.id, u);
        remoteCursors.clear();
        renderUsers();
        requestRender();
        break;
      }
      case 'add':
        if (!shapes.has(m.shape.id)) shapes.set(m.shape.id, m.shape);
        requestRender();
        break;
      case 'update': {
        const s = shapes.get(m.shape.id);
        if (s) {
          for (const k of Object.keys(s)) delete s[k];
          Object.assign(s, m.shape);
        } else {
          shapes.set(m.shape.id, m.shape);
        }
        requestRender();
        break;
      }
      case 'delete':
        shapes.delete(m.id);
        if (selectedId === m.id) selectedId = null;
        if (dragInfo && dragInfo.id === m.id) dragInfo = null;
        requestRender();
        break;
      case 'clear':
        shapes.clear();
        selectedId = null;
        requestRender();
        break;
      case 'user-joined':
        users.set(m.user.id, m.user);
        renderUsers();
        toast(m.user.name + ' 加入了白板');
        break;
      case 'user-left': {
        const u = users.get(m.id);
        users.delete(m.id);
        remoteCursors.delete(m.id);
        renderUsers();
        if (u) toast(u.name + ' 离开了白板');
        break;
      }
      case 'cursor':
        if (m.id !== selfId) {
          remoteCursors.set(m.id, { x: m.x, y: m.y, name: m.name, color: m.color, ts: Date.now() });
          requestRender();
        }
        break;
      case 'error':
        recvErrors.push({ t: Date.now(), msg: m.message });
        toast(m.message || '服务器错误');
        break;
      default:
        break;
    }
  }

  window.addEventListener('beforeunload', () => { try { ws && ws.close(); } catch (e) { /* ignore */ } });

  // ===== 房间号 =====
  function genRoomId() {
    const a = new Uint8Array(4);
    crypto.getRandomValues(a);
    return Array.from(a, (b) => b.toString(16).padStart(2, '0')).join('');
  }
  (function initRoom() {
    const u = new URL(location.href);
    let rid = u.searchParams.get('room');
    if (!rid || !/^[A-Za-z0-9_-]{1,64}$/.test(rid)) {
      rid = genRoomId();
      u.searchParams.set('room', rid);
      history.replaceState(null, '', u);
    }
    roomId = rid;
  })();

  // ===== 调试探针（供自动化验证用） =====
  window.__wb = {
    count: () => shapes.size,
    shapes: () => [...shapes.values()],
    tool: () => tool,
    roomId: () => roomId,
    users: () => users.size,
    selfId: () => selfId,
    connected: () => !!(ws && ws.readyState === WebSocket.OPEN),
    wsState: () => (ws ? ws.readyState : -1),
    sent: () => sendLog.slice(-20),
    recvErrors: () => recvErrors,
    undoDepth: () => undoStack.length,
    redoDepth: () => redoStack.length,
    selected: () => selectedId,
    setTool,
    doUndo,
    doRedo,
  };

  // ===== 启动 =====
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  connect();
})();
