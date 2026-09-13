/* make-compact-probe.js —— 生成 _verify/probe-compact.html：
 * 在真实浏览器中跑一遍关键路径，把结论渲染成大号短行放在页面顶部，便于截图后肉眼准确读取。
 * 覆盖：视口宽度 / 横向溢出 / 溢出元素数 / 媒体查询命中 / 4 个快捷按钮的真实 click 结果 / 主数字。
 * 同时保留完整 JSON 版本 _probe.html（供需要原始数据时查看）。
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
  var R = [], err = '';
  try {
    var t=document.getElementById('total'), p=document.getElementById('people');
    var res=document.getElementById('result'), big=document.getElementById('bigAmount');
    var hint=document.getElementById('totalHint'), linesEl=document.getElementById('lines');

    var vw=window.innerWidth, de=document.documentElement;
    var bad=[], all=document.querySelectorAll('*');
    for (var i=0;i<all.length;i++){
      var el=all[i], r=el.getBoundingClientRect();
      if (r.width===0 && r.height===0) continue;
      if (r.right>vw+0.5 || r.left<-0.5) bad.push(el.tagName+(el.id?'#'+el.id:'')+'@'+r.right.toFixed(0));
    }
    R.push('VIEWPORT  innerWidth=' + vw
      + '  docScrollWidth=' + de.scrollWidth
      + '  bodyScrollWidth=' + document.body.scrollWidth
      + '  horizontalOverflow=' + (de.scrollWidth > vw+1)
      + '  media(max-560)=' + window.matchMedia('(max-width: 560px)').matches
      + '  overflowEls=' + bad.length + ' [' + bad.join(',') + ']');

    var btns=document.querySelectorAll('.quick button');
    R.push('BUTTONS  .quick button count=' + btns.length);

    if (btns.length===4) {
      btns[2].click();
      R.push('CLICK#3(边界:人数0)  total="' + t.value + '" people="' + p.value
        + '" errClass=' + res.classList.contains('err')
        + ' status="' + linesEl.textContent + '"');

      btns[1].click();
      R.push('CLICK#2(128.555元/3人)  total="' + t.value + '" people="' + p.value
        + '" hintHas规整=' + (hint.textContent.indexOf('规整')>=0)
        + ' big="' + big.textContent + '"');

      btns[0].click();
      R.push('CLICK#1(1000元/7人)  total="' + t.value + '" people="' + p.value
        + '" big="' + big.textContent + '" errClass=' + res.classList.contains('err'));

      btns[3].click();
      R.push('CLICK#4(清空)  total="' + t.value + '" people="' + p.value
        + '" status="' + linesEl.textContent + '"');
    }

    // 余数为 0 时主数字是否带（基准）
    t.value='88.88'; p.value='4';
    t.dispatchEvent(new Event('input'));
    R.push('EXACT(88.88元/4人)  big="' + big.textContent + '"');
  } catch(e) { err = 'PROBE_EXCEPTION: ' + (e && e.message ? e.message : String(e)); }

  var box=document.createElement('div');
  box.id='PROBE_COMPACT';
  box.textContent = R.join('\\n') + (err ? '\\n' + err : '');
  box.style.cssText='position:absolute;left:0;top:0;width:100%;z-index:99999;margin:0;padding:8px;'
    +'background:#fffbe6;color:#111;font:13px/1.5 Consolas,monospace;white-space:pre-wrap;'
    +'word-break:break-all;border-bottom:3px solid #d33;';
  document.body.style.position='relative';
  document.body.insertBefore(box, document.body.firstChild);
})();
</script>`;

const header = `<style>
  #PROBE_PAD { height: 0; }
  body { padding-top: 190px !important; }
</style>`;

fs.writeFileSync(path.join(dir, 'probe-compact.html'),
  html.replace('</head>', header + '</head>').replace('</body>', PROBE + '\n</body>'), 'utf8');
console.log('probe-compact.html written');
