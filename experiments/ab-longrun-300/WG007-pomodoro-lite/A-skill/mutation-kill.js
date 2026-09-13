"use strict";
// Mutation-kill against pomodoro.html pure core.
// Each mutation is applied to a temp HTML file; verify-logic extracts and must go red.
var fs = require("fs");
var path = require("path");
var os = require("os");
var { spawnSync } = require("child_process");

var root = __dirname;
var htmlSrc = fs.readFileSync(path.join(root, "pomodoro.html"), "utf8");
var verifier = path.join(root, "verify-logic.js");
var verifierSrc = fs.readFileSync(verifier, "utf8");

var mutations = [
  {
    name: "parseMinutes accepts 0 (drop MIN check)",
    from: "if (i < MIN_MINUTES || i > MAX_MINUTES) return null;",
    to: "if (i > MAX_MINUTES) return null;"
  },
  {
    name: "formatMs floors instead of ceils",
    from: "var totalSec = Math.ceil(ms / 1000);",
    to: "var totalSec = Math.floor(ms / 1000);"
  },
  {
    name: "remainingFrom does not clamp negative",
    from: "return left > 0 ? left : 0;",
    to: "return left;"
  },
  {
    name: "finish status string wrong",
    from: 'status: "时间到"',
    to: 'status: "结束"'
  },
  {
    name: "pause never fires from running",
    from: 'if (action === "pause") {',
    to: 'if (action === "never_pause") {'
  },
  {
    name: "default minutes not 25",
    from: "var DEFAULT_MINUTES = 25;",
    to: "var DEFAULT_MINUTES = 30;"
  }
];

function runOnce(htmlText, verifierText, tag) {
  var tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pomo-mut-"));
  var tmpHtml = path.join(tmpDir, "pomodoro.html");
  var tmpVer = path.join(tmpDir, "verify-logic.js");
  fs.writeFileSync(tmpHtml, htmlText);
  fs.writeFileSync(tmpVer, verifierText);
  var r = spawnSync(process.execPath, [tmpVer], { encoding: "utf8" });
  try {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  } catch (e) { /* ignore */ }
  return r;
}

// control: unmutated must pass
var control = runOnce(htmlSrc, verifierSrc, "control");
if (control.status !== 0) {
  console.log("CONTROL FAILED — verifier does not pass on clean HTML");
  console.log(control.stdout || "");
  console.log(control.stderr || "");
  process.exit(1);
}
console.log("CONTROL PASS (clean HTML -> green)");

var killed = 0;
var survived = [];

mutations.forEach(function (m) {
  if (htmlSrc.indexOf(m.from) === -1) {
    survived.push(m.name + " (pattern not found)");
    console.log("SURVIVED", m.name, "(pattern not found)");
    return;
  }
  var mutatedHtml = htmlSrc.split(m.from).join(m.to);
  // verifier reads pomodoro.html from its own directory — we put both in tmp
  var r = runOnce(mutatedHtml, verifierSrc, m.name);
  if (r.status !== 0) {
    killed++;
    console.log("KILLED ", m.name);
  } else {
    survived.push(m.name);
    console.log("SURVIVED", m.name);
  }
});

console.log("---");
console.log("killed", killed + "/" + mutations.length);
if (survived.length) {
  console.log("survived:", survived.join("; "));
  process.exit(1);
}
console.log("mutation-kill PASS");
