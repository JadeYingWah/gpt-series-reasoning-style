const fs = require('fs');
const html = fs.readFileSync('<实验根目录>/ab-longrun-300/WG003-pomodoro-lite/B-noskill/pomodoro.html', 'utf8');
const checks = [];
const ext = html.match(/<script[^>]+src=|<link[^>]+href=|<img[^>]+src=\s*["']https?:/gi);
checks.push(['no external script/link/img tags', !ext]);
['display', 'status', 'btnStart', 'btnPause', 'btnReset', 'minutes', 'btnApply'].forEach(function (id) {
  checks.push(['id ' + id + ' present', html.indexOf('id="' + id + '"') !== -1]);
});
checks.push(['时间到 status string', html.indexOf('时间到') !== -1]);
checks.push(['range 1-60', html.indexOf('min="1"') !== -1 && html.indexOf('max="60"') !== -1]);
checks.push(['default 25:00 text', html.indexOf('25:00') !== -1]);
checks.push(['Web Audio beep present', html.indexOf('AudioContext') !== -1]);
checks.push(['no http/https URLs', !/https?:\/\//i.test(html)]);
let fail = 0;
checks.forEach(function (c) {
  console.log((c[1] ? 'PASS' : 'FAIL') + ': ' + c[0]);
  if (!c[1]) fail++;
});
process.exit(fail ? 1 : 0);
