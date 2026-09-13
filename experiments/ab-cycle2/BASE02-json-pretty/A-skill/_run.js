const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");
const scripts = ["verify-json-tool.js", "browser-verify.js"];
let out = "";
for (const s of scripts) {
  const r = spawnSync(process.execPath, [path.join(__dirname, s)], { cwd: __dirname, encoding: "utf8", maxBuffer: 32 * 1024 * 1024 });
  out += "### " + s + "\nstatus=" + r.status + " signal=" + r.signal +
    "\n--- STDOUT ---\n" + (r.stdout || "") + "\n--- STDERR ---\n" + (r.stderr || "") +
    "\nerror=" + (r.error ? String(r.error) : "none") + "\n\n";
}
fs.writeFileSync(path.join(__dirname, "_run.log"), out, "utf8");
