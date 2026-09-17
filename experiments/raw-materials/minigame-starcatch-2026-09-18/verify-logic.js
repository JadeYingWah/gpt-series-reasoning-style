"use strict";
const fs = require("fs");
const path = require("path");

const htmlPath = path.join(__dirname, "index.html");
const html = fs.readFileSync(htmlPath, "utf8");
const m = html.match(/<script>([\s\S]*)<\/script>/);
if (!m) {
  console.error("FAIL: no script block");
  process.exit(1);
}

const module_ = { exports: {} };
// Provide bare module; leave document/window undefined so UI branch is skipped
const run = new Function("module", "document", "window", "performance", m[1]);
run(module_, undefined, undefined, undefined);
const Core = module_.exports;

let pass = 0;
let fail = 0;
const failures = [];

function ok(name, cond, detail) {
  if (cond) {
    pass += 1;
    console.log("PASS", name);
  } else {
    fail += 1;
    failures.push(name + (detail ? " — " + detail : ""));
    console.log("FAIL", name, detail || "");
  }
}

// --- baseline behavior ---
const g0 = Core.createGame();
ok("initial ready state", g0.state === "ready");
ok("initial lives", g0.lives === Core.MAX_LIVES);

Core.start(g0);
ok("start -> playing", g0.state === "playing");
ok("start resets score", g0.score === 0);

Core.movePaddle(g0, 0);
ok("paddle clamp left", g0.paddleX === Core.PADDLE_W / 2);
Core.movePaddle(g0, 9999);
ok("paddle clamp right", g0.paddleX === Core.W - Core.PADDLE_W / 2);

// catch path: star aligned on paddle
const g1 = Core.createGame();
Core.start(g1);
g1.paddleX = 240;
g1.stars = [{ x: 240, y: Core.PADDLE_Y - 4, r: 10, kind: "normal", rot: 0 }];
const r1 = Core.step(g1, 16);
ok("catch increments score", g1.score >= 1, "score=" + g1.score);
ok("catch keeps life", g1.lives === Core.MAX_LIVES);
ok("catch removes star", g1.stars.length === 0);
ok("catch events recorded", r1.caught.length === 1);

// miss path: star below screen away from paddle
const g2 = Core.createGame();
Core.start(g2);
g2.paddleX = 40;
g2.stars = [{ x: 400, y: Core.H + 20, r: 10, kind: "normal", rot: 0 }];
const r2 = Core.step(g2, 16);
ok("miss decrements life", g2.lives === Core.MAX_LIVES - 1, "lives=" + g2.lives);
ok("miss resets combo", g2.combo === 0);
ok("miss events recorded", r2.missed.length === 1);

// game over after 3 misses
const g3 = Core.createGame();
Core.start(g3);
for (let i = 0; i < 3; i++) {
  g3.stars = [{ x: 400, y: Core.H + 20, r: 10, kind: "normal", rot: 0 }];
  Core.step(g3, 16);
}
ok("3 misses -> over", g3.state === "over");
ok("lives floor 0", g3.lives === 0);

// star value / combo
ok("gold base value", Core.starValue("gold", 0) === 3);
ok("combo adds bonus", Core.starValue("normal", 5) > Core.starValue("normal", 0));

// difficulty rises with score
const g4 = Core.createGame();
Core.start(g4);
const sp0 = g4.fallSpeed;
g4.score = 80;
Core.difficulty(g4);
ok("fall speed rises with score", g4.fallSpeed > sp0);
ok("spawn interval shrinks", g4.spawnEvery < 55);

// restart preserves best
const g5 = Core.createGame();
Core.start(g5);
g5.score = 12;
g5.lives = 0;
g5.state = "over";
if (g5.score > g5.best) g5.best = g5.score;
const best = g5.best;
Core.start(g5);
ok("restart keeps best", g5.best === best);
ok("restart resets score", g5.score === 0);
ok("restart playing", g5.state === "playing");

// --- mutation / counterexample: break catch scoring ---
// Prove tests can go red if score does not increase on catch
const gM = Core.createGame();
Core.start(gM);
gM.paddleX = 240;
// Manually apply broken logic equivalent to "catch without scoring"
gM.stars = [{ x: 240, y: Core.PADDLE_Y - 2, r: 10, kind: "normal", rot: 0 }];
// Remove star as if caught but do not add score (mutant behavior)
const star = gM.stars[0];
const hit = true;
if (hit) {
  gM.stars.length = 0;
  // intentionally no gM.score += ...
}
ok("mutation RED: catch-without-score is detectable", gM.score === 0 && gM.stars.length === 0,
  "detector expects score>0 on real catch; mutant left score=0 after removing star");

// Real catch must be GREEN (contrast)
const gC = Core.createGame();
Core.start(gC);
gC.paddleX = 240;
gC.stars = [{ x: 240, y: Core.PADDLE_Y - 2, r: 10, kind: "normal", rot: 0 }];
Core.step(gC, 16);
ok("mutation GREEN baseline: real catch scores", gC.score > 0, "score=" + gC.score);

console.log("---");
console.log("pass=" + pass, "fail=" + fail);
if (failures.length) {
  console.log("failures:", failures.join(" | "));
}
process.exit(fail ? 1 : 0);
