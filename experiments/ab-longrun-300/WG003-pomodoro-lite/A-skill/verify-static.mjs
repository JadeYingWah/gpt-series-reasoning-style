// Static scan of shipped HTML: no CDN/external URLs; required IDs and strings present.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const html = fs.readFileSync(path.join(__dirname, 'pomodoro.html'), 'utf8');

let pass = 0;
let fail = 0;
function check(name, ok) {
  if (ok) {
    pass++;
    console.log('PASS: ' + name);
  } else {
    fail++;
    console.log('FAIL: ' + name);
  }
}

check('no http/https URLs', !/https?:\/\//i.test(html));
check('no external script src', !/<script[^>]+src=/i.test(html));
check('no external link href', !/<link[^>]+href=/i.test(html));
check('no external img src', !/<img[^>]+src=/i.test(html));
check('no CDN markers', !/cdn\.|unpkg|jsdelivr|googleapis|bootstrapcdn/i.test(html));

['display', 'status', 'btnStart', 'btnPause', 'btnReset', 'minutes', 'btnApply'].forEach((id) => {
  check('id ' + id + ' present', html.indexOf('id="' + id + '"') !== -1);
});

check('default 25:00 text', html.indexOf('25:00') !== -1);
check('时间到 status string', html.indexOf('时间到') !== -1);
check('start/pause/reset handlers', ['btnStart', 'btnPause', 'btnReset'].every((id) => html.indexOf(id) !== -1));
check('range min=1 max=60 on input', /min="1"/.test(html) && /max="60"/.test(html));
check('AudioContext beep present', html.indexOf('AudioContext') !== -1);
check('absolute endAt countdown', html.indexOf('endAt = Date.now() + remainingMs') !== -1);
check('single inline script', (html.match(/<script/gi) || []).length === 1);

console.log('');
console.log('pass=' + pass + ' fail=' + fail);
process.exit(fail ? 1 : 0);
