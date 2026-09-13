/* make-previews.js —— 生成带预填值的预览页（派生自 app.html，仅作视觉验收证据）。
 * 预览 = app.html 原文 + 追加一段「设置输入值并派发 input 事件」的脚本，不改动任何业务逻辑。
 * 运行：node make-previews.js
 */
'use strict';
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, '_verify');
fs.mkdirSync(dir, { recursive: true });

const html = fs.readFileSync(path.join(__dirname, 'app.html'), 'utf8');

const cases = [
  ['01-empty', '', '', '空态：提示未崩溃'],
  ['02-1000-7', '1000', '7', '1000 元 / 7 人（有余数）'],
  ['03-128.555-3', '128.555', '3', '超 2 位小数规整 + 余数'],
  ['04-people-0', '300', '0', '人数 0：提示不崩'],
  ['05-exact', '88.88', '4', '整除：无余数'],
  ['06-too-large', '9'.repeat(60), '5', '超长输入：TOO_LARGE'],
  ['07-mobile-1000-7', '1000', '7', '移动端窄屏 390px'],
];

const manifest = [];
cases.forEach(([name, total, people, desc]) => {
  const inject = `
<script>
(function(){
  var t=document.getElementById('total'), p=document.getElementById('people');
  t.value=${JSON.stringify(total)}; p.value=${JSON.stringify(people)};
  t.dispatchEvent(new Event('input')); p.dispatchEvent(new Event('input'));
})();
</script>`;
  const out = html.replace('</body>', inject + '\n</body>');
  const file = path.join(dir, name + '.html');
  fs.writeFileSync(file, out, 'utf8');
  manifest.push({ name, total, people, desc, file });
});

fs.writeFileSync(path.join(dir, 'manifest.json'),
  JSON.stringify(manifest, null, 2), 'utf8');
console.log('generated ' + manifest.length + ' previews');
