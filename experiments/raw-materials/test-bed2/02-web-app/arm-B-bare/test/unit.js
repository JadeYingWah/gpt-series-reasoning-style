/**
 * unit.js — 前端纯逻辑模块的 Node 侧单元验证（history / shapes）。
 * 这两个模块不含 DOM 顶层依赖，可直接在 Node 中 import。
 */
import { History } from "../public/js/history.js";
import { makeShape, hitTest, boundsOf } from "../public/js/shapes.js";

let passed = 0;
function ok(cond, name) {
  if (!cond) throw new Error(`ASSERT FAIL: ${name}`);
  passed++;
  console.log(`  ✓ ${name}`);
}

const rect = (id) => makeShape("rect", id, 0, 0, 10, 10, { stroke: "#000" });

/* History：add/remove/update 的撤销与重做 */
{
  const h = new History();
  const s = rect("a");
  h.push({ kind: "add", shape: s }, null);
  ok(h.canUndo() && !h.canRedo(), "add 入栈后可撤销、不可重做");

  const undoOp = h.popUndo();
  ok(undoOp.kind === "remove" && undoOp.shape.id === "a", "撤销 add = remove 同一图形");
  ok(!h.canUndo() && h.canRedo(), "撤销后栈状态翻转");

  const redoOp = h.popRedo();
  ok(redoOp.kind === "add" && redoOp.shape.id === "a", "重做恢复 add");

  // update：撤销应回到旧值
  const h2 = new History();
  const before = rect("b");           // (0,0)-(10,10)
  const after = { ...before, x2: 99 };
  h2.push({ kind: "update", shape: after }, before);
  const u = h2.popUndo();
  ok(u.kind === "update" && u.shape.x2 === 10, "撤销 update 恢复旧值");
  const r = h2.popRedo();
  ok(r.kind === "update" && r.shape.x2 === 99, "重做 update 回到新值");

  // 新操作清空 redo
  const h3 = new History();
  h3.push({ kind: "add", shape: rect("c") }, null);
  h3.popUndo();
  h3.push({ kind: "add", shape: rect("d") }, null);
  ok(!h3.canRedo(), "新操作提交后重做栈清空");
}

/* shapes：命中测试与边界 */
{
  const s = rect("hit");
  ok(hitTest(s, 5, 5), "点在矩形内部命中");
  ok(!hitTest(s, 50, 50), "远离矩形不命中");
  ok(hitTest(s, -3, 5), "容差内边缘命中");

  const e = makeShape("ellipse", "e", 0, 0, 10, 10, {});
  ok(hitTest(e, 5, 5), "椭圆心命中");
  ok(!hitTest(e, 5, 18), "远离椭圆（超出容差）不命中");
  ok(hitTest(e, 5, 9.5), "椭圆边界容差内命中");

  const a = makeShape("arrow", "a", 0, 0, 100, 100, {});
  ok(hitTest(a, 50, 50), "箭头线段中点命中");
  ok(!hitTest(a, 50, 70), "箭头线段外不命中");

  const b = boundsOf(makeShape("rect", "b2", 100, 200, 40, 80, {}));
  ok(b.x === 40 && b.y === 80 && b.w === 60 && b.h === 120, "boundsOf 归一化负向矩形");
}

console.log(`\nUNIT PASS — ${passed} 项断言通过`);
