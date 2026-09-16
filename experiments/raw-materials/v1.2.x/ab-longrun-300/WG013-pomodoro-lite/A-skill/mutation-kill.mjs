/**
 * Mutation-kill probe for verify-logic.mjs
 * Injects known defects into a copy of the pure core and asserts
 * that at least one original assertion class turns red.
 * Original pomodoro.html is never modified.
 */
import { readFileSync, writeFileSync, mkdirSync, copyFileSync, rmSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

const __dirname = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(__dirname, 'pomodoro.html'), 'utf8');
const verifySrc = readFileSync(join(__dirname, 'verify-logic.mjs'), 'utf8');

const mutants = [
  {
    id: 'm01-off-by-one-minutes',
    // clamp allows 0 and 61
    find: 'if (n < MIN_MINUTES || n > MAX_MINUTES) return null;',
    replace: 'if (n < 0 || n > 61) return null;'
  },
  {
    id: 'm02-format-floor-not-ceil',
    find: 'var totalSec = Math.max(0, Math.ceil(ms / 1000));',
    replace: 'var totalSec = Math.max(0, Math.floor(ms / 1000));'
  },
  {
    id: 'm03-pause-does-not-freeze',
    find: 'state.remainingMs = remainingFromEndAt(state.endAt, now);',
    replace: '/* mutant: do not freeze */;'
  },
  {
    id: 'm04-done-label-wrong',
    find: "if (status === 'done') return '时间到';",
    replace: "if (status === 'done') return '完成';"
  },
  {
    id: 'm05-tick-never-completes',
    find: 'if (isFinished(state.remainingMs)) {\n        state.remainingMs = 0;\n        state.endAt = null;\n        state.status = \'done\';\n      }',
    replace: '/* mutant: never transition to done */'
  }
];

const outDir = join(__dirname, '_mutants');
mkdirSync(outDir, { recursive: true });

let killed = 0;
const results = [];

for (const m of mutants) {
  if (!html.includes(m.find)) {
    results.push({ id: m.id, killed: false, reason: 'pattern not found in source' });
    console.log('SKIP  ' + m.id + ' (pattern not found)');
    continue;
  }
  const mutated = html.replace(m.find, m.replace);
  if (mutated === html) {
    results.push({ id: m.id, killed: false, reason: 'replace was no-op' });
    console.log('SKIP  ' + m.id + ' (no-op replace)');
    continue;
  }
  const dir = join(outDir, m.id);
  mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, 'pomodoro.html'), mutated, 'utf8');
  // rewrite verify to read local pomodoro.html (same relative name)
  writeFileSync(join(dir, 'verify-logic.mjs'), verifySrc, 'utf8');
  try {
    execFileSync(process.execPath, [join(dir, 'verify-logic.mjs')], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe']
    });
    // exit 0 → mutant survived
    results.push({ id: m.id, killed: false, reason: 'verify still passed' });
    console.log('LIVE  ' + m.id);
  } catch (e) {
    const out = (e.stdout || '') + (e.stderr || '');
    const failLines = out.split(/\r?\n/).filter((l) => l.includes('FAIL'));
    killed += 1;
    results.push({ id: m.id, killed: true, failCount: failLines.length, sample: failLines.slice(0, 3) });
    console.log('KILL  ' + m.id + '  (' + failLines.length + ' FAIL lines)');
    if (failLines[0]) console.log('       ' + failLines[0].trim());
  }
}

console.log('---');
console.log('Kill rate: ' + killed + '/' + mutants.length + ' = ' + Math.round((killed / mutants.length) * 100) + '%');

// keep mutation evidence; do not delete _mutants (evidence artifact)
writeFileSync(
  join(outDir, 'mutation-report.json'),
  JSON.stringify({ killed, total: mutants.length, results }, null, 2),
  'utf8'
);

if (killed < mutants.length) {
  process.exit(1);
}
process.exit(0);
