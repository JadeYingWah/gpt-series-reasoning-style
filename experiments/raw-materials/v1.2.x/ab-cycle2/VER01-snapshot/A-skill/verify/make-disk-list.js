// 生成交付目录磁盘清单；自身大小用定长占位符回填，保证清单内容与真实字节数一致
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');
const SELF = 'verify/disk-list.txt';
const TOKEN = '######'; // 6 字符定长占位，替换后长度不变

const lines = [];
(function walk(dir, rel) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    const p = path.join(dir, e.name);
    const r = rel ? rel + '/' + e.name : e.name;
    if (e.isDirectory()) { lines.push(r + '/'); walk(p, r); }
    else if (r !== SELF) { lines.push(r + '  (' + fs.statSync(p).size + ' B)'); }
  }
})(root, '');

// 自身行插回原排序位置
const selfLine = SELF + '  (' + TOKEN + ' B)';
const sorted = [...lines, selfLine].sort((a, b) =>
  a.split('  (')[0].localeCompare(b.split('  (')[0]));
const template = sorted.join('\n') + '\n';
const size = Buffer.byteLength(template, 'utf8');
const finalText = template.replace(TOKEN, String(size).padStart(TOKEN.length));
if (Buffer.byteLength(finalText, 'utf8') !== size) throw new Error('清单自指大小回填后长度发生变化');

fs.writeFileSync(path.join(__dirname, 'disk-list.txt'), finalText);
console.log('ok size=' + size);
