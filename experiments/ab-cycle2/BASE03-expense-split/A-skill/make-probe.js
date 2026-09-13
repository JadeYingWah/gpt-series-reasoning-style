/* make-probe.js —— 生成 _verify/_probe.html：预填 1000/7 后，
 * 把视口宽度、文档滚动宽度、以及对横向溢出有责任的元素清单写入 <pre id="PROBE_RESULT">，
 * 供 chrome --headless --dump-dom 输出后解析。
 */
'use strict';
const fs = require('fs');
const path = require('path');
const dir = path.join(__dirname, '_verify');
fs.mkdirSync(dir, { recursive: true });

const html = fs.readFileSync(path.join(__dirname, 'app.html'), 'utf8');

const inject = `
<script>
(function(){
  var t=document.getElementById('total'), p=document.getElementById('people');
  t.value='1000'; p.value='7';
  t.dispatchEvent(new Event('input')); p.dispatchEvent(new Event('input'));

  var vw = window.innerWidth;
  var de = document.documentElement;
  var bad = [];
  var all = document.querySelectorAll('*');
  for (var i=0;i<all.length;i++){
    var el = all[i];
    var r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    if (r.right > vw + 0.5 || r.left < -0.5) {
      bad.push(el.tagName + (el.id ? '#'+el.id : '') + (el.className ? '.'+String(el.className).split(' ').join('.') : '')
        + ' [left=' + r.left.toFixed(1) + ' right=' + r.right.toFixed(1) + ' w=' + r.width.toFixed(1) + ']');
    }
  }
  var out = {
    innerWidth: vw,
    clientWidth: de.clientWidth,
    scrollWidth: de.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    mediaMax560: window.matchMedia('(max-width: 560px)').matches,
    overflowCount: bad.length,
    offenders: bad.slice(0, 25)
  };
  var pre = document.createElement('pre');
  pre.id = 'PROBE_RESULT';
  pre.textContent = 'PROBE_JSON_BEGIN\n' + JSON.stringify(out, null, 2) + '\nPROBE_JSON_END';
  pre.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:8px;'
    + 'background:#fff;color:#000;font:10px/1.35 monospace;white-space:pre-wrap;'
    + 'max-width:100vw;max-height:100vh;overflow:auto;border:2px solid red;';
  document.body.appendChild(pre);
})();
</script>`;

fs.writeFileSync(path.join(dir, '_probe.html'), html.replace('</body>', inject + '\n</body>'), 'utf8');
console.log('probe written');
