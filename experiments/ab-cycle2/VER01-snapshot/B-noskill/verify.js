/* 验证脚本：抽取 tool.html 中的 SORT_CORE 纯逻辑并断言行为。
   运行：node verify.js     （零依赖） */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

const HTML = path.join(__dirname, "tool.html");
const html = fs.readFileSync(HTML, "utf8");

let pass = 0;
const fails = [];
function ok(name, cond, extra) {
  if (cond) { pass++; console.log("PASS  " + name); }
  else { fails.push(name + (extra ? "  <- " + extra : "")); console.log("FAIL  " + name + (extra ? "  <- " + extra : "")); }
}

/* --- 1. 结构检查 --- */
ok("文件存在且非空", html.length > 500, "len=" + html.length);
ok("声明 <!DOCTYPE html>", /^<!DOCTYPE html>/i.test(html.trim()));
ok("含表头容器 #head-row", html.includes('id="head-row"'));
ok("含表体容器 #body", html.includes('id="body"'));
ok("无外部依赖（无 src=/href= 外链）", !/<script[^>]+src=|<link[^>]+href=/i.test(html));
ok("数据渲染使用 textContent（非 innerHTML 拼接）", html.includes("td.textContent") && !/\.innerHTML\s*=/.test(html));

/* --- 2. 抽取 SORT_CORE 并做语法检查 --- */
const m = html.match(/\/\* ==== SORT_CORE:BEGIN[\s\S]*?\*\/([\s\S]*?)\/\* ==== SORT_CORE:END ==== \*\//);
ok("能抽到 SORT_CORE 区块", !!m);
if (!m) { report(); process.exit(1); }
const core = m[1];

const allScript = html.match(/<script>([\s\S]*?)<\/script>/);
ok("能抽到 <script> 区块", !!allScript);
if (allScript) {
  const tmp = path.join(__dirname, ".extracted-script.js");
  fs.writeFileSync(tmp, allScript[1]);
  const r = require("child_process").spawnSync(process.execPath, ["--check", tmp], { encoding: "utf8" });
  ok("整段脚本通过 node --check（语法合法）", r.status === 0, (r.stderr || "").trim().split("\n")[0]);
  fs.unlinkSync(tmp);
}

const ctx = {};
vm.createContext(ctx);
vm.runInContext(core + "\n;globalThis.__api = { DATA, COLUMNS, sortRows, compareValues };", ctx);
const { DATA, COLUMNS, sortRows, compareValues } = ctx.__api;

/* --- 3. 数据检查 --- */
ok("记录数为 5", DATA.length === 5, "got " + DATA.length);
ok("列数为 6", COLUMNS.length === 6, "got " + COLUMNS.length);
ok("每行都含全部列字段", DATA.every(r => COLUMNS.every(c => Object.prototype.hasOwnProperty.call(r, c.key))));
ok("名称列无重复（便于肉眼核验排序）", new Set(DATA.map(r => r.name)).size === DATA.length);

/* --- 4. 排序行为检查 --- */
const keys = COLUMNS.map(c => c.key);
const asc = k => sortRows(DATA, k, "asc").map(r => r[k]);
const desc = k => sortRows(DATA, k, "desc").map(r => r[k]);
const isSorted = (arr, cmp) => arr.every((v, i) => i === 0 || cmp(arr[i - 1], v) <= 0);

for (const col of COLUMNS) {
  const a = asc(col.key);
  const c = col.type === "string"
    ? (x, y) => new Intl.Collator("zh-Hans-CN", { numeric: true, sensitivity: "base" }).compare(x, y)
    : (x, y) => (x < y ? -1 : x > y ? 1 : 0);
  ok("升序有序: " + col.key, isSorted(a.map(v => col.type === "date" ? Date.parse(v) : v), c), JSON.stringify(a));
  const d = desc(col.key);
  ok("降序有序: " + col.key, isSorted(d.map(v => col.type === "date" ? Date.parse(v) : v), (x, y) => c(y, x)), JSON.stringify(d));
  ok("升降序互为逆序: " + col.key, JSON.stringify(a) === JSON.stringify([...d].reverse()));
}

// 关键：数值列必须按数值而非字典序（qty = 42,8,15,120,3 字典序会错）
ok("数量列按数值排序（非字典序）", JSON.stringify(asc("qty")) === JSON.stringify([3, 8, 15, 42, 120]), JSON.stringify(asc("qty")));
ok("单价列按数值排序", JSON.stringify(asc("price")) === JSON.stringify([89.5, 259.9, 499, 1299, 1899]), JSON.stringify(asc("price")));
ok("日期列按时间排序", JSON.stringify(asc("date")) === JSON.stringify(["2025-11-30", "2026-01-07", "2026-03-14", "2026-05-22", "2026-07-02"]), JSON.stringify(asc("date")));

// 不可变性 + 长度守恒
const before = JSON.stringify(DATA);
sortRows(DATA, "price", "desc");
ok("sortRows 不修改入参", JSON.stringify(DATA) === before);
ok("排序结果长度守恒", sortRows(DATA, "name", "asc").length === DATA.length);

// 稳定性（同值保持原相对次序）
const tie = sortRows(DATA, "category", "asc");
const tieOk = tie.filter(r => r.category === "外设").map(r => r.id).join(",") === "1,2";
ok("同值保持稳定次序（外设 id 1 在 2 前）", tieOk, tie.map(r => r.id + ":" + r.category).join(" "));

// 空值排最后
ok("空值排在升序末尾", compareValues(null, 5, "number") === 1);
ok("空值排在降序末尾（取反后仍由 dir 处理）", compareValues(5, null, "number") === -1);

// 非法列名应报错
let threw = false;
try { sortRows(DATA, "nope", "asc"); } catch (e) { threw = true; }
ok("未知列名抛错", threw);

function report() {
  console.log("\n" + pass + " passed, " + fails.length + " failed");
  if (fails.length) { console.log("失败项："); fails.forEach(f => console.log("  - " + f)); }
}
report();
process.exit(fails.length ? 1 : 0);
