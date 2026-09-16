/**
 * history.js — 撤销/重做栈。
 *
 * 思路：记录每个已提交操作对应的 undo op 与 redo op：
 *   add(shape)    ↔ remove(shape)
 *   remove(shape) ↔ add(shape)
 *   update(new)   ↔ update(prev)
 * 多用户场景下只撤销“自己产生”的操作（远端 op 不调用 push），
 * 避免把协作者刚画的内容撤掉。
 *
 * op 结构：{ kind: "add"|"update"|"remove", shape }
 */
export class History {
  constructor() {
    /** @type {{undo: op, redo: op}[]} */
    this.undoStack = [];
    /** @type {op[]} */
    this.redoStack = [];
  }

  /**
   * 记录一个刚由本人提交的操作。
   * @param {op} op        已提交的操作（shape 为新值）
   * @param {shape|null} prevShape update 操作必须提供旧值，其余传 null
   */
  push(op, prevShape = null) {
    let undo, redo;
    switch (op.kind) {
      case "add":
        undo = { kind: "remove", shape: op.shape };
        redo = { kind: "add", shape: op.shape };
        break;
      case "remove":
        undo = { kind: "add", shape: op.shape };
        redo = { kind: "remove", shape: op.shape };
        break;
      case "update":
        undo = { kind: "update", shape: prevShape };
        redo = { kind: "update", shape: op.shape };
        break;
      default:
        return;
    }
    this.undoStack.push({ undo, redo });
    if (this.undoStack.length > 500) this.undoStack.shift();
    this.redoStack.length = 0;
  }

  canUndo() { return this.undoStack.length > 0; }
  canRedo() { return this.redoStack.length > 0; }

  /** 返回撤销时要执行的操作；栈空返回 null。 */
  popUndo() {
    const entry = this.undoStack.pop();
    if (!entry) return null;
    this.redoStack.push(entry.redo);
    return entry.undo;
  }

  /** 返回重做时要执行的操作；栈空返回 null。 */
  popRedo() {
    const op = this.redoStack.pop();
    if (!op) return null;
    // 重做的逆即对应 undo（undo 栈里 shape 存的是旧值，这里补上新值引用）
    this.undoStack.push({ undo: invertOf(op), redo: op });
    return op;
  }

  clear() {
    this.undoStack.length = 0;
    this.redoStack.length = 0;
  }
}

/** 由一个待执行的 op 推导其逆（仅用于重放入栈）。 */
function invertOf(op) {
  switch (op.kind) {
    case "add":    return { kind: "remove", shape: op.shape };
    case "remove": return { kind: "add", shape: op.shape };
    case "update": return { kind: "update", shape: op.shape };
    default:       return op;
  }
}
