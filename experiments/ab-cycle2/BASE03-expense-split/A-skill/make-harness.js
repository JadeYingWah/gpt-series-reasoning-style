/* make-harness.js —— 生成 _verify/harness.html。
 * 目的：Windows 上 Chrome headless 窗口有最小宽度限制，直接 --window-size=390 会被裁切。
 * 用 iframe 把内层文档的「布局视口」固定为 390/480/760 px，从而真实验证响应式与横向溢出。
 * 每个 iframe 内跑一个带 try/catch 的探针，把 innerWidth / scrollWidth / 溢出元素清单渲染成可见浮层。
 */
'use strict';
const fs = require('fs');
const path = require('path');

const dir = path.join(__dirname, '_verify');
fs.mkdirSync(dir, { recursive: true });
const html = fs.readFileSync(path.join(__dirname, 'app.html'), 'utf8');

const PROBE = `
<script>
(function(){
  var out = { note: 'probe for app.html' };
  try {
    var t=document.getElementById('total'), p=document.getElementById('people');
    out.hasInputs = !!t && !!p;
    if (t && p) {
      t.value='1000'; p.value='7';
      t.dispatchEvent(new Event('input')); p.dispatchEvent(new Event('input'));
    }
    var vw = window.innerWidth, de = document.documentElement;
    var bad = [], all = document.querySelectorAll('*');
    for (var i=0;i<all.length;i++){
      var el = all[i], r = el.getBoundingClientRect();
      if (r.width === 0 && r.height === 0) continue;
      if (r.right > vw + 0.5 || r.left < -0.5) {
        bad.push(el.tagName + (el.id ? '#'+el.id : '')
          + ' r=' + r.right.toFixed(0) + ' w=' + r.width.toFixed(0));
      }
    }
    // 真实浏览器中执行快捷按钮的 click 回调
    var btns = document.querySelectorAll('.quick button');
    out.quickButtonCount = btns.length;
    if (btns.length === 4) {
      btns[2].click();                                  // 「边界：人数 0」
      out.afterBtn3 = { total: t.value, people: p.value,
                        err: document.getElementById('result').classList.contains('err') };
      btns[1].click();                                  // 「128.555 元 / 3 人」
      out.afterBtn2 = { total: t.value, people: p.value,
                        hint: document.getElementById('totalHint').textContent };
      btns[0].click();                                  // 「1000 元 / 7 人」
    }
    out.afterBtn1 = { total: t.value, people: p.value,
                      big: (document.getElementById('bigAmount')||{}).textContent || '',
                      err: document.getElementById('result').classList.contains('err') };

    out.innerWidth = vw;
    out.docScrollWidth = de.scrollWidth;
    out.bodyScrollWidth = document.body ? document.body.scrollWidth : null;
    out.mediaMax560 = window.matchMedia('(max-width: 560px)').matches;
    out.horizontalOverflow = (de.scrollWidth > vw + 1);
    out.overflowingElementCount = bad.length;
    out.offenders = bad.slice(0, 12);
    out.bigAmount = (document.getElementById('bigAmount')||{}).textContent || '';
    out.statusLines = (document.getElementById('lines')||{}).textContent || '';
    out.errorState = (document.getElementById('result')||{classList:{contains:function(){return null}}})
      .classList.contains('err');
  } catch (e) {
    out.probeError = String(e && e.message ? e.message : e);
    out.probeErrorStack = String(e && e.stack ? e.stack : '').split('\\n').slice(0,3).join(' | ');
  }
  var pre = document.createElement('pre');
  pre.id = 'PROBE_RESULT';
  pre.textContent = JSON.stringify(out, null, 1);
  pre.style.cssText = 'position:fixed;left:0;top:0;z-index:99999;margin:0;padding:6px;'
    + 'background:#fff;color:#000;font:9px/1.3 monospace;white-space:pre-wrap;'
    + 'width:100%;max-height:100%;overflow:hidden;border-bottom:2px solid red;';
  if (document.body) document.body.appendChild(pre);
})();
</script>`;

const probeFile = path.join(dir, '_probe.html');
fs.writeFileSync(probeFile, html.replace('</body>', PROBE + '\n</body>'), 'utf8');

const widths = [390, 480, 760];
let frames = '';
widths.forEach(w => {
  const h = w <= 480 ? 1180 : 940;
  frames += `
  <figure>
    <figcaption>如果框宽 ${w}px（<code>_probe.html</code> 预填 1000 元 / 7 人）</figcaption>
    <iframe src="_probe.html" width="${w}" height="${h}" style="width:${w}px;height:${h}px"></iframe>
  </figure>`;
});

const harness = `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>响应式验收 harness</title>
<style>
 body{margin:0;padding:14px;background:#e9edf5;color:#111;
      font-family:"Segoe UI","Microsoft YaHei",sans-serif;}
 h1{font-size:15px;margin:0 0 10px;}
 .row{display:flex;gap:16px;align-items:flex-start;flex-wrap:nowrap;}
 figure{margin:0;background:#fff;border:1px solid #b9c3d4;border-radius:8px;padding:8px;}
 figcaption{font-size:11px;color:#445;margin-bottom:6px;font-weight:600;}
 iframe{border:1px solid #d33;display:block;background:#0f1420;}
</style></head><body>
<h1>响应式验收：白底红框浮层为 _probe.html 内测得的真实布局视口数据（iframe 内布局视口 = 指定宽度）</h1>
<div class="row">${frames}
</div>
</body></html>`;

fs.writeFileSync(path.join(dir, 'harness.html'), harness, 'utf8');
console.log('harness written with widths ' + widths.join(','));

/* 高清单框确认图：360 / 390 两个极窄宽度，配合 --force-device-scale-factor=2 便于读探针文本 */
const narrow = [320, 360, 390];
let nf = '';
narrow.forEach(w => {
  nf += `
  <figure>
    <figcaption>${w}px</figcaption>
    <iframe src="_probe.html" width="${w}" height="1240" style="width:${w}px;height:1240px"></iframe>
  </figure>`;
});
fs.writeFileSync(path.join(dir, 'harness-narrow.html'), `<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><title>极窄宽度验收</title>
<style>
 body{margin:0;padding:12px;background:#e9edf5;font-family:"Segoe UI","Microsoft YaHei",sans-serif;}
 .row{display:flex;gap:14px;align-items:flex-start;}
 figure{margin:0;background:#fff;border:1px solid #b9c3d4;border-radius:8px;padding:6px;}
 figcaption{font-size:12px;font-weight:700;color:#334;margin-bottom:5px;}
 iframe{border:1px solid #d33;display:block;background:#0f1420;}
</style></head><body><div class="row">${nf}</div></body></html>`, 'utf8');
console.log('narrow harness written with widths ' + narrow.join(','));
