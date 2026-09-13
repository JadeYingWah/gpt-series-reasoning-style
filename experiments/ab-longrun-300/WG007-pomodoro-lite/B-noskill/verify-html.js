"use strict";
var fs = require("fs");
var path = "<实验根目录>/ab-longrun-300/WG007-pomodoro-lite/B-noskill/pomodoro.html";
var html = fs.readFileSync(path, "utf8");
var bad = [];

if (/https?:\/\//i.test(html)) bad.push("http(s) URL");
if (/<script[^>]+src=/i.test(html)) bad.push("script src");
if (/<link[^>]+href=/i.test(html)) bad.push("link href");
if (/cdn\./i.test(html)) bad.push("cdn");
if (/require\s*\(/.test(html)) bad.push("require");

["时间到", "开始", "暂停", "重置", "继续", "就绪", "进行中", "已暂停"].forEach(function (s) {
  if (html.indexOf(s) === -1) bad.push("missing string: " + s);
});

if (html.indexOf('min="1"') === -1) bad.push("missing min=1");
if (html.indexOf('max="60"') === -1) bad.push("missing max=60");

["react", "vue", "jquery", "angular"].forEach(function (w) {
  if (new RegExp(w, "i").test(html)) bad.push("framework: " + w);
});

// structural markers
var markers = {
  beep: /AudioContext/,
  wallClock: /endTime\s*-\s*Date\.now/,
  setInterval: /setInterval/,
  clearInterval: /clearInterval/,
  finishedStatus: /时间到/,
  default25: /25/,
};
Object.keys(markers).forEach(function (k) {
  if (!markers[k].test(html)) bad.push("missing marker: " + k);
});

if (bad.length) {
  console.log("ISSUES:", bad);
  process.exit(1);
}
console.log("HTML static checks PASS");
console.log("bytes", html.length);
console.log("single external script tags:", (html.match(/<script/g) || []).length);
console.log("has AudioContext beep: true");
console.log("has wall-clock endTime: true");
