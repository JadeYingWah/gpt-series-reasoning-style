"use strict";
var fs = require("fs");
var path = require("path");
var file = path.join(__dirname, "pomodoro.html");
var html = fs.readFileSync(file, "utf8");
var bad = [];

// no external resources
if (/https?:\/\//i.test(html)) bad.push("http(s) URL present");
if (/<script[^>]+\bsrc\s*=/i.test(html)) bad.push("script src present");
if (/<link[^>]+\bhref\s*=/i.test(html)) bad.push("link href present");
if (/\bcdn\./i.test(html)) bad.push("cdn host present");
if (/<img[^>]+\bsrc\s*=/i.test(html)) bad.push("img src present");
if (/import\s+/.test(html)) bad.push("ES module import present");

// frameworks
["react", "vue", "jquery", "angular", "bootstrap", "tailwind"].forEach(function (w) {
  if (new RegExp("\\b" + w + "\\b", "i").test(html)) bad.push("framework token: " + w);
});

// required UI strings
[
  "时间到",
  "开始",
  "暂停",
  "重置",
  "继续",
  "就绪",
  "进行中",
  "已暂停",
  "25:00"
].forEach(function (s) {
  if (html.indexOf(s) === -1) bad.push("missing string: " + s);
});

// config bounds
if (!/min="1"/.test(html)) bad.push('missing min="1"');
if (!/max="60"/.test(html)) bad.push('missing max="60"');
if (!/value="25"/.test(html)) bad.push('missing default value="25"');

// structural markers of correct timer design
var markers = {
  wallClock: /remainingFrom|endTime\s*-\s*Date\.now/,
  setInterval: /setInterval/,
  clearInterval: /clearInterval/,
  audioBeep: /AudioContext/,
  stateMachine: /STATES\./,
  finishedStatus: /时间到/,
  defaultMinutes: /DEFAULT_MINUTES\s*=\s*25/,
  pureParse: /function parseMinutes/,
  pureFormat: /function formatMs/,
  pureTransition: /function transition/
};
Object.keys(markers).forEach(function (k) {
  if (!markers[k].test(html)) bad.push("missing marker: " + k);
});

// single inline script, no src
var scriptTags = html.match(/<script\b[^>]*>/gi) || [];
if (scriptTags.length !== 1) bad.push("expected exactly 1 script tag, got " + scriptTags.length);
scriptTags.forEach(function (t) {
  if (/\bsrc\s*=/i.test(t)) bad.push("script tag has src");
});

if (bad.length) {
  console.log("ISSUES:");
  bad.forEach(function (b) { console.log(" -", b); });
  process.exit(1);
}
console.log("HTML static checks PASS");
console.log("bytes", Buffer.byteLength(html, "utf8"));
console.log("script tags", scriptTags.length);
console.log("external refs 0");
console.log("markers", Object.keys(markers).join(", "));
