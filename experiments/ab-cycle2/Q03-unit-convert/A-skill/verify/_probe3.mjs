import fs from 'node:fs';
import path from 'node:path';
const out = [];
const cands = [
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
];
for (const c of cands) out.push(`browser ${fs.existsSync(c) ? 'FOUND ' : 'missing'} ${c}`);
// jsdom / playwright / puppeteer 是否可用
for (const m of ['jsdom', 'playwright', 'puppeteer']) {
  try {
    out.push(`module ${m} -> ${require.resolve ? 'n/a' : ''}${import.meta.resolve ? import.meta.resolve(m) : ''}`);
  } catch (e) { out.push(`module ${m} -> NOT FOUND`); }
}
fs.writeFileSync(path.join(import.meta.dirname, '_probe3.txt'), out.join('\n') + '\n', 'utf8');
