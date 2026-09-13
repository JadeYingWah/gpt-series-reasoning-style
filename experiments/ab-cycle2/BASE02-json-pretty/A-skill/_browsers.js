const fs = require("fs");
const cands = [
  "C:/Program Files/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
  process.env.LOCALAPPDATA + "/Google/Chrome/Application/chrome.exe",
  "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe",
  "C:/Program Files/Microsoft/Edge/Application/msedge.exe",
];
const out = cands.map(p => (p && fs.existsSync(p) ? "YES " : "no  ") + p);
fs.writeFileSync(__dirname + "/_browsers.txt", out.join("\n") + "\n", "utf8");
