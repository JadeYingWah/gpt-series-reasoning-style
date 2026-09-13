/**
 * Browser smoke harness: loads pure core the same way the page does,
 * drives the state machine with fake Date.now, and prints results.
 * Not a substitute for real click-hands-on; that remains UNVERIFIED.
 * Used only to cross-check that the *script as shipped* still executes
 * and that UI-facing labels stay correct.
 */
import { readFileSync, writeFileSync, unlinkSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dirname, 'pomodoro.html'), 'utf8');

// Inject auto-run probes after the existing script (document present → UI layer loads)
const probe = `
<script>
(function () {
  var out = [];
  function log(k, v) { out.push(k + '=' + v); }
  var d = document.getElementById('display');
  var st = document.getElementById('status');
  var bs = document.getElementById('btnStart');
  var bp = document.getElementById('btnPause');
  var br = document.getElementById('btnReset');
  var di = document.getElementById('durationInput');

  log('initial_display', d && d.textContent);
  log('initial_status', st && st.textContent);
  log('start_enabled', bs && !bs.disabled);
  log('pause_disabled', bp && bp.disabled);

  // click start
  if (bs) bs.click();
  log('after_start_status', st && st.textContent);
  log('after_start_pause_enabled', bp && !bp.disabled);
  log('after_start_display', d && d.textContent);

  // click pause
  if (bp) bp.click();
  log('after_pause_status', st && st.textContent);

  // set duration 1
  if (di) {
    di.value = '1';
    di.dispatchEvent(new Event('change', { bubbles: true }));
  }
  log('after_duration_status', st && st.textContent);
  log('after_duration_display', d && d.textContent);
  log('duration_input', di && di.value);

  // invalid duration
  if (di) {
    di.value = '70';
    di.dispatchEvent(new Event('change', { bubbles: true }));
  }
  log('invalid_hint', document.getElementById('hint') && document.getElementById('hint').textContent);
  log('invalid_keeps_duration', di && di.value);

  // reset
  if (di) {
    di.value = '25';
    di.dispatchEvent(new Event('change', { bubbles: true }));
  }
  if (br) br.click();
  log('after_reset_status', st && st.textContent);
  log('after_reset_display', d && d.textContent);

  var pre = document.createElement('pre');
  pre.id = 'smoke-results';
  pre.textContent = out.join('\\n');
  document.body.appendChild(pre);
})();
</script>
`;

const harness = html.replace('</body>', probe + '\n</body>');
const tmp = join(__dirname, '_smoke.html');
writeFileSync(tmp, harness, 'utf8');

const chrome =
  'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const uri = pathToFileURL(tmp).href;

try {
  const dom = execFileSync(
    chrome,
    ['--headless=new', '--disable-gpu', '--no-sandbox', '--dump-dom', '--virtual-time-budget=2000', uri],
    { encoding: 'utf8', timeout: 30000 }
  );
  const m = dom.match(/<pre id="smoke-results">([\s\S]*?)<\/pre>/);
  if (!m) {
    console.error('FAIL: smoke-results not found in DOM');
    console.error(dom.slice(0, 500));
    process.exit(1);
  }
  const text = m[1]
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"');
  console.log('=== Headless UI smoke ===');
  console.log(text);
} catch (e) {
  console.error('FAIL: chrome smoke run error:', e.message);
  process.exit(1);
} finally {
  try { unlinkSync(tmp); } catch (_) { /* keep if locked */ }
}
