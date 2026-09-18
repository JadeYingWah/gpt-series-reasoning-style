(() => {
  "use strict";

  const BPM = 120;
  const BEAT = 60 / BPM;
  const LEAD_IN = 2.0;
  const APPROACH = 1.6;
  const JUDGE_PERFECT = 0.08;
  const JUDGE_GREAT = 0.14;
  const KEY_MAP = { d: 0, f: 1, j: 2, k: 3 };
  const LANE_LABEL = ["米", "蛋", "葱", "酱"];

  const PATTERN = [
    [0], [1], [2], [3],
    [0], [1], [2], [3],
    [0, 2], [1], [0, 2], [3],
    [0], [1, 3], [2], [],
    [0], [1], [2], [3],
    [0, 3], [1, 2], [0], [1],
    [2], [3], [0, 2], [1, 3],
    [0], [], [1], [2],
    [3], [2], [1], [0],
    [0, 1], [2, 3], [0, 1], [2, 3],
    [0], [1], [0], [2],
    [3], [2], [1], [0],
    [0, 2], [1, 3], [0, 2], [1, 3],
    [0], [1], [2], [3],
    [0, 1, 2], [3], [0], [1, 2],
    [3], [0], [1], [2],
    [0], [2], [1], [3],
    [0, 3], [1, 2], [0], [1],
    [2], [3], [0, 2], [1, 3],
    [0], [1], [2], [3],
    [0, 2], [1, 3], [0, 1, 2, 3], [],
    [0], [1], [2], [3],
    [0], [1], [2], [3],
  ];

  const $ = (id) => document.getElementById(id);
  const screens = {
    title: $("screen-title"),
    howto: $("screen-howto"),
    play: $("screen-play"),
    result: $("screen-result"),
  };

  const els = {
    score: $("hud-score"),
    combo: $("hud-combo"),
    progress: $("hud-progress"),
    judge: $("judge"),
    noteLayer: $("note-layer"),
    receptorRow: $("receptor-row"),
    lanes: $("lanes"),
    char: $("char-img"),
    potFood: $("pot-food"),
    resultRank: $("result-rank"),
    resultTitle: $("result-title"),
    resultScore: $("result-score"),
    resultPerfect: $("result-perfect"),
    resultGreat: $("result-great"),
    resultMiss: $("result-miss"),
    resultCombo: $("result-combo"),
  };

  let audioCtx = null;
  let state = null;
  let raf = 0;
  let judgeTimer = 0;

  function showScreen(name) {
    Object.entries(screens).forEach(([key, el]) => {
      const on = key === name;
      el.hidden = !on;
      el.classList.toggle("is-active", on);
    });
  }

  function ensureAudio() {
    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === "suspended") audioCtx.resume();
    return audioCtx;
  }

  function tone(freq, when, dur, type, gain) {
    const ctx = ensureAudio();
    const t0 = ctx.currentTime + when;
    const osc = ctx.createOscillator();
    const g = ctx.createGain();
    osc.type = type || "sine";
    osc.frequency.setValueAtTime(freq, t0);
    g.gain.setValueAtTime(0.0001, t0);
    g.gain.exponentialRampToValueAtTime(gain || 0.08, t0 + 0.01);
    g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    osc.connect(g).connect(ctx.destination);
    osc.start(t0);
    osc.stop(t0 + dur + 0.02);
  }

  function playHit(kind) {
    if (kind === "perfect") {
      tone(880, 0, 0.12, "triangle", 0.1);
      tone(1320, 0.03, 0.1, "triangle", 0.06);
    } else if (kind === "great") {
      tone(660, 0, 0.1, "triangle", 0.08);
    } else {
      tone(140, 0, 0.16, "square", 0.05);
    }
  }

  function scheduleBeatClicks(chartEnd, startDelaySec) {
    const ctx = ensureAudio();
    const totalBeats = Math.ceil(chartEnd / BEAT);
    const offset = Math.max(0, startDelaySec || 0);
    for (let i = 0; i < totalBeats; i++) {
      const when = offset + i * BEAT;
      const t0 = ctx.currentTime + when;
      const osc = ctx.createOscillator();
      const g = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(i % 4 === 0 ? 220 : 165, t0);
      g.gain.setValueAtTime(0.0001, t0);
      g.gain.exponentialRampToValueAtTime(i % 4 === 0 ? 0.05 : 0.025, t0 + 0.005);
      g.gain.exponentialRampToValueAtTime(0.0001, t0 + 0.08);
      osc.connect(g).connect(ctx.destination);
      osc.start(t0);
      osc.stop(t0 + 0.1);
    }
  }

  function buildChart() {
    const notes = [];
    let beatIndex = 0;
    for (const group of PATTERN) {
      for (const lane of group) {
        notes.push({
          id: notes.length,
          lane,
          time: LEAD_IN + beatIndex * BEAT,
          hit: false,
          missed: false,
          el: null,
        });
      }
      beatIndex += 1;
    }
    return notes;
  }

  function resetState() {
    const notes = buildChart();
    const chartEnd = LEAD_IN + PATTERN.length * BEAT + 1;
    notes.sort((a, b) => a.time - b.time || a.lane - b.lane);
    return {
      notes,
      chartEnd,
      startPerf: 0,
      score: 0,
      combo: 0,
      maxCombo: 0,
      perfect: 0,
      great: 0,
      miss: 0,
      total: notes.length,
      running: false,
      done: false,
      activeEls: [],
    };
  }

  function spawnNoteEls() {
    els.noteLayer.innerHTML = "";
    const lanes = els.lanes.getBoundingClientRect();
    const pad = 12;
    const gap = 10;
    const count = 4;
    const laneW = (lanes.width - pad * 2 - gap * (count - 1)) / count;

    for (const n of state.notes) {
      const el = document.createElement("div");
      el.className = `note lane-${n.lane}`;
      el.textContent = LANE_LABEL[n.lane];
      el.style.width = `${laneW}px`;
      el.style.marginLeft = `${pad + n.lane * (laneW + gap)}px`;
      el.dataset.id = String(n.id);
      els.noteLayer.appendChild(el);
      n.el = el;
      state.activeEls.push(n);
    }
  }

  function receptorTop() {
    const row = els.receptorRow.getBoundingClientRect();
    const lanes = els.lanes.getBoundingClientRect();
    return row.top - lanes.top + row.height / 2 - 18;
  }

  function updateHud() {
    els.score.textContent = String(state.score);
    els.combo.textContent = String(state.combo);
    const progress = state.total ? (state.perfect + state.great + state.miss) / state.total : 0;
    const pct = Math.round(progress * 100);
    els.progress.style.width = `${pct}%`;
    els.potFood.style.height = `${pct}%`;
  }

  function flashJudge(text, kind) {
    els.judge.textContent = text;
    els.judge.classList.remove("is-show", "is-perfect", "is-great", "is-miss");
    void els.judge.offsetWidth;
    els.judge.classList.add("is-show", `is-${kind}`);
    clearTimeout(judgeTimer);
    judgeTimer = setTimeout(() => {
      els.judge.classList.remove("is-show");
    }, 420);
  }

  function flashReceptor(lane) {
    const rec = els.receptorRow.querySelector(`[data-lane="${lane}"]`);
    if (!rec) return;
    rec.classList.add("is-flash");
    setTimeout(() => rec.classList.remove("is-flash"), 120);
  }

  function cheer(hit) {
    els.char.classList.remove("is-hit", "is-miss");
    void els.char.offsetWidth;
    els.char.classList.add(hit ? "is-hit" : "is-miss");
  }

  function applyJudge(note, delta) {
    if (note.hit || note.missed) return;
    const abs = Math.abs(delta);
    let kind;
    if (abs <= JUDGE_PERFECT) {
      kind = "perfect";
      state.perfect += 1;
      state.score += 300 + state.combo * 2;
      state.combo += 1;
      flashJudge("Perfect", "perfect");
      playHit("perfect");
      cheer(true);
    } else if (abs <= JUDGE_GREAT) {
      kind = "great";
      state.great += 1;
      state.score += 150 + state.combo;
      state.combo += 1;
      flashJudge("Great", "great");
      playHit("great");
      cheer(true);
    } else {
      kind = "miss";
      state.miss += 1;
      state.combo = 0;
      flashJudge("Miss", "miss");
      playHit("miss");
      cheer(false);
    }
    if (kind === "miss") {
      note.missed = true;
    } else {
      note.hit = true;
    }
    state.maxCombo = Math.max(state.maxCombo, state.combo);
    flashReceptor(note.lane);
    if (note.el) {
      note.el.classList.add("is-gone");
      setTimeout(() => note.el && note.el.remove(), 120);
    }
    updateHud();
  }

  function tryHit(lane) {
    if (!state || !state.running) return;
    const now = (performance.now() - state.startPerf) / 1000;
    let best = null;
    let bestAbs = Infinity;
    for (const n of state.notes) {
      if (n.lane !== lane || n.hit || n.missed) continue;
      const d = now - n.time;
      const a = Math.abs(d);
      if (a < bestAbs) {
        bestAbs = a;
        best = n;
      }
      if (n.time - now > JUDGE_GREAT + 0.05) break;
    }
    const lanes = document.querySelectorAll(".lane");
    if (lanes[lane]) lanes[lane].classList.add("is-lit");
    setTimeout(() => {
      if (lanes[lane]) lanes[lane].classList.remove("is-lit");
    }, 100);

    if (best && bestAbs <= JUDGE_GREAT) {
      applyJudge(best, now - best.time);
    }
  }

  function frame() {
    if (!state || !state.running) return;
    const now = (performance.now() - state.startPerf) / 1000;
    const top = receptorTop();
    const travelTop = 0;

    for (const n of state.notes) {
      if (n.hit || n.missed || !n.el) continue;
      const until = n.time - now;
      if (until > APPROACH + 0.2) {
        n.el.style.transform = "translateY(-80px)";
        n.el.style.opacity = "0";
        continue;
      }
      n.el.style.opacity = "1";
      const p = 1 - until / APPROACH;
      const y = travelTop + p * (top - travelTop);
      n.el.style.transform = `translateY(${y}px)`;

      if (now - n.time > JUDGE_GREAT) {
        applyJudge(n, now - n.time);
      }
    }

    const last = state.notes[state.notes.length - 1];
    const allJudged = state.perfect + state.great + state.miss >= state.total;
    if (now > state.chartEnd || (allJudged && last && now > last.time + 0.4)) {
      finish();
      return;
    }

    raf = requestAnimationFrame(frame);
  }

  function startGame() {
    ensureAudio();
    cancelAnimationFrame(raf);
    clearTimeout(judgeTimer);
    state = resetState();
    showScreen("play");
    requestAnimationFrame(() => {
      spawnNoteEls();
      updateHud();
      els.judge.classList.remove("is-show");
      setTimeout(() => {
        const delay = 0.06;
        scheduleBeatClicks(state.chartEnd, delay);
        state.startPerf = performance.now() + delay * 1000;
        state.running = true;
        raf = requestAnimationFrame(frame);
      }, 80);
    });
  }

  function finish() {
    if (!state || state.done) return;
    state.done = true;
    state.running = false;
    cancelAnimationFrame(raf);

    const acc = state.total ? (state.perfect + state.great * 0.7) / state.total : 0;
    let rank = "C";
    let title = "糊锅边缘…再来一次";
    if (acc >= 0.95 && state.miss <= 2) {
      rank = "S";
      title = "完美出锅！指挥得漂亮";
    } else if (acc >= 0.85) {
      rank = "A";
      title = "起锅成功，香气扑鼻";
    } else if (acc >= 0.65) {
      rank = "B";
      title = "能吃，但拍子还差一点";
    }

    els.resultRank.textContent = rank;
    els.resultRank.classList.toggle("is-s", rank === "S");
    els.resultTitle.textContent = title;
    els.resultScore.textContent = String(state.score);
    els.resultPerfect.textContent = String(state.perfect);
    els.resultGreat.textContent = String(state.great);
    els.resultMiss.textContent = String(state.miss);
    els.resultCombo.textContent = String(state.maxCombo);

    showScreen("result");
  }

  function quitGame() {
    if (state) {
      state.running = false;
      state.done = true;
    }
    cancelAnimationFrame(raf);
    showScreen("title");
  }

  $("btn-start").addEventListener("click", startGame);
  $("btn-start-2").addEventListener("click", startGame);
  $("btn-howto").addEventListener("click", () => showScreen("howto"));
  $("btn-back-title").addEventListener("click", () => showScreen("title"));
  $("btn-retry").addEventListener("click", startGame);
  $("btn-to-title").addEventListener("click", () => showScreen("title"));
  $("btn-quit").addEventListener("click", quitGame);

  window.addEventListener("keydown", (e) => {
    if (e.repeat) return;
    const k = e.key.toLowerCase();
    if (k in KEY_MAP) {
      e.preventDefault();
      tryHit(KEY_MAP[k]);
    } else if (k === "escape" && state && state.running) {
      quitGame();
    } else if ((k === "enter" || k === " ") && screens.title.classList.contains("is-active")) {
      e.preventDefault();
      startGame();
    }
  });

  document.querySelectorAll(".lane").forEach((lane) => {
    const idx = Number(lane.dataset.lane);
    lane.addEventListener("pointerdown", (e) => {
      e.preventDefault();
      tryHit(idx);
    });
  });

  showScreen("title");
})();
