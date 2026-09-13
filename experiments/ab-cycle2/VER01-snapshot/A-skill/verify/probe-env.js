// 环境探测：找出可用于真实浏览器验证的工具
const fs = require('fs');
const path = require('path');
const out = { node: process.version, browsers: [], modules: [], npx: [] };

const candidates = [
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  process.env.LOCALAPPDATA + '/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
];
for (const c of candidates) {
  try { if (c && fs.existsSync(c)) out.browsers.push(c); } catch (e) {}
}

// 全局 node_modules 中是否有可用库
const globalRoots = [
  path.join(process.env.APPDATA || '', 'npm/node_modules'),
  path.join(process.env.USERPROFILE || '', 'node_modules'),
];
for (const root of globalRoots) {
  try {
    if (!fs.existsSync(root)) continue;
    for (const name of fs.readdirSync(root)) {
      if (/puppeteer|playwright|jsdom|happy-dom|linkedom/i.test(name)) {
        out.modules.push(path.join(root, name));
      }
    }
  } catch (e) {}
}

fs.writeFileSync(path.join(__dirname, 'probe-env.json'), JSON.stringify(out, null, 2));
