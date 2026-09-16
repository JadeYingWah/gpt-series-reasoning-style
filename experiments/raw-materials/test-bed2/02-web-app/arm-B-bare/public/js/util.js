/** util.js — 小工具函数。 */

/** 生成 url-safe 随机 id。 */
export function randId(len = 8) {
  const chars = "abcdefghijkmnpqrstuvwxyz23456789";
  let out = "";
  const arr = new Uint8Array(len);
  crypto.getRandomValues(arr);
  for (let i = 0; i < len; i++) out += chars[arr[i] % chars.length];
  return out;
}

/** 节流包装。 */
export function throttle(fn, ms) {
  let last = 0, timer = null, lastArgs = null;
  return (...args) => {
    lastArgs = args;
    const now = Date.now();
    const run = () => { last = Date.now(); timer = null; fn(...lastArgs); };
    if (now - last >= ms) run();
    else if (!timer) timer = setTimeout(run, ms - (now - last));
  };
}

/** 简易 toast 提示。 */
export function toast(text, ms = 1800) {
  const el = document.getElementById("toast");
  if (!el) return;
  el.textContent = text;
  el.classList.add("show");
  clearTimeout(el._timer);
  el._timer = setTimeout(() => el.classList.remove("show"), ms);
}
