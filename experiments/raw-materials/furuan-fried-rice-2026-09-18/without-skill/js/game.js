(() => {
  "use strict";

  const STEPS = [
    { name: "热锅倒油", icon: "🫗", speed: 1.1, good: 0.22, perfect: 0.08, heat: 4 },
    { name: "打入鸡蛋", icon: "🥚", speed: 1.2, good: 0.2, perfect: 0.075, heat: 6 },
    { name: "倒入米饭", icon: "🍚", speed: 1.25, good: 0.2, perfect: 0.07, heat: 6 },
    { name: "加火腿丁", icon: "🍖", speed: 1.35, good: 0.18, perfect: 0.065, heat: 5 },
    { name: "撒葱花", icon: "🧅", speed: 1.4, good: 0.18, perfect: 0.06, heat: 5 },
    { name: "大火翻炒", icon: "🔥", type: "toss", tossCount: 3, speed: 1.45, good: 0.18, perfect: 0.06, heat: 14 },
    { name: "淋酱油", icon: "🥢", speed: 1.5, good: 0.17, perfect: 0.055, heat: 6 },
    { name: "点点盐", icon: "🧂", speed: 1.55, good: 0.16, perfect: 0.05, heat: 5 },
    { name: "完美颠勺", icon: "✨", type: "toss", tossCount: 4, speed: 1.6, good: 0.16, perfect: 0.05, heat: 16 },
    { name: "出锅装盘", icon: "🍽️", speed: 1.5, good: 0.18, perfect: 0.06, heat: -10 },
  ];

  const LINES = {
    start: [
      "开火开火！今天也要炒出闪闪发光的饭！",
      "食材都排好队了，就等你按节拍～",
      "弗糯糯秘传：锅气足，才叫炒饭！",
    ],
    perfect: [
      "完美！就是这个节奏！",
      "哇，米粒都在发光！",
      "好厉害，锅气都追着你跑！",
      "这手法……是天才吧？！",
      "香到隔壁都来敲门啦！",
    ],
    good: [
      "不错不错，稳住～",
      "还行还行，再利落一点！",
      "有那味儿了，继续！",
      "节奏感越来越好了！",
    ],
    miss: [
      "哎呀，糊掉了啦！",
      "手滑了……再来一次好不好？",
      "锅铲抗议了哦！",
      "专注专注，鼻子都熏到了！",
    ],
    hot: [
      "锅气要爆了！小心烫！",
      "火太猛啦，稳住翻炒！",
    ],
    done: [
      "装盘！快看看成色！",
      "最后一铲，收官～",
    ],
  };

  const RESULT_COMMENTS = {
    s: "「这就是传说中的黄金蛋炒饭！弗糯糯认证 · 传说级！」",
    a: "「相当出色的锅气！再来一点点火花就是满分啦。」",
    b: "「及格是及格……下次别让锅铲飞出去哦。」",
    c: "「嗯……焦香也是香（心虚）。我们再练一盘？」",
  };

  const $ = (id) => document.getElementById(id);

  const els = {
    screens: {
      title: $("screen-title"),
      game: $("screen-game"),
      result: $("screen-result"),
    },
    btnStart: $("btn-start"),
    btnRetry: $("btn-retry"),
    btnHome: $("btn-home"),
    btnHit: $("btn-hit"),
    hudScore: $("hud-score"),
    hudCombo: $("hud-combo"),
    hudStepIndex: $("hud-step-index"),
    hudStepTotal: $("hud-step-total"),
    hudStepName: $("hud-step-name"),
    heatFill: $("heat-fill"),
    heatBar: document.querySelector(".heat-bar"),
    recipeList: $("recipe-list"),
    dialogueText: $("dialogue-text"),
    charImg: $("char-img"),
    marker: $("marker"),
    zoneGood: $("zone-good"),
    zonePerfect: $("zone-perfect"),
    timingTrack: $("timing-track"),
    timingHint: $("timing-hint"),
    tossPips: $("toss-pips"),
    wok: $("wok"),
    wokFood: $("wok-food"),
    wokFlame: $("wok-flame"),
    wokZone: $("wok-zone"),
    judgePop: $("judge-pop"),
    floatLayer: $("float-layer"),
    canvas: $("fx-canvas"),
    resultTitle: $("result-title"),
    resultStars: $("result-stars"),
    resultScore: $("result-score"),
    resultCombo: $("result-combo"),
    resultPerfect: $("result-perfect"),
    resultMiss: $("result-miss"),
    resultComment: $("result-comment"),
  };

  els.hudStepTotal.textContent = String(STEPS.length);

  const state = {
    running: false,
    stepIndex: 0,
    tossHit: 0,
    score: 0,
    combo: 0,
    maxCombo: 0,
    perfect: 0,
    good: 0,
    miss: 0,
    heat: 18,
    // marker
    markerPos: 0.08,
    markerDir: 1,
    markerSpeed: 0.7,
    zoneCenter: 0.5,
    goodW: 0.22,
    perfectW: 0.08,
    awaitingInput: false,
    raf: 0,
    lastT: 0,
    settleTimer: 0,
  };

  const particles = [];
  let ctx = null;
  let dpr = 1;

  function rand(arr) {
    return arr[(Math.random() * arr.length) | 0];
  }

  function showScreen(name) {
    Object.entries(els.screens).forEach(([key, el]) => {
      el.classList.toggle("active", key === name);
    });
  }

  function buildRecipe() {
    els.recipeList.innerHTML = "";
    STEPS.forEach((s, i) => {
      const li = document.createElement("li");
      li.dataset.index = String(i);
      li.innerHTML = `<span class="step-no">${i + 1}</span><span>${s.icon} ${s.name}</span>`;
      els.recipeList.appendChild(li);
    });
  }

  function setDialogue(text) {
    els.dialogueText.textContent = text;
  }

  function setCharMood(mood) {
    els.charImg.classList.remove("cheer", "dismay");
    if (mood) els.charImg.classList.add(mood);
  }

  function updateHUD() {
    els.hudScore.textContent = String(state.score);
    els.hudCombo.textContent = `×${state.combo}`;
    els.hudStepIndex.textContent = String(Math.min(state.stepIndex + 1, STEPS.length));
    els.hudStepName.textContent = STEPS[Math.min(state.stepIndex, STEPS.length - 1)].name;
    const pct = Math.max(0, Math.min(100, state.heat));
    els.heatFill.style.width = `${pct}%`;
    els.heatBar.classList.toggle("hot", pct >= 85);
  }

  function updateRecipe() {
    [...els.recipeList.children].forEach((li, i) => {
      li.classList.remove("active", "done", "fail");
      if (i < state.stepIndex) li.classList.add("done");
      else if (i === state.stepIndex) li.classList.add("active");
    });
  }

  function layoutZones() {
    const step = STEPS[state.stepIndex];
    state.goodW = step.good;
    state.perfectW = step.perfect;
    // place zone slightly randomized left/right of center
    const bias = (Math.random() - 0.5) * 0.35;
    state.zoneCenter = Math.min(0.78, Math.max(0.22, 0.5 + bias));

    const trackW = els.timingTrack.clientWidth || 400;
    const goodPx = state.goodW * trackW;
    const perfectPx = state.perfectW * trackW;
    const centerPx = state.zoneCenter * trackW;

    els.zoneGood.style.left = `${centerPx - goodPx / 2}px`;
    els.zoneGood.style.width = `${goodPx}px`;
    els.zonePerfect.style.left = `${centerPx - perfectPx / 2}px`;
    els.zonePerfect.style.width = `${perfectPx}px`;

    // marker starts from an edge opposite travel
    state.markerPos = Math.random() > 0.5 ? 0.04 : 0.96;
    state.markerDir = state.markerPos < 0.5 ? 1 : -1;
    state.markerSpeed = step.speed * (0.92 + Math.random() * 0.16);
  }

  function showJudge(kind) {
    const labels = { perfect: "完美！", good: "不错", miss: "失误" };
    els.judgePop.textContent = labels[kind];
    els.judgePop.className = `judge-pop ${kind}`;
    // reflow to restart animation
    void els.judgePop.offsetWidth;
    els.judgePop.classList.add("show");
  }

  function floatText(text, color) {
    const span = document.createElement("span");
    span.className = "float-text";
    span.textContent = text;
    span.style.left = `${35 + Math.random() * 30}%`;
    span.style.top = `${30 + Math.random() * 25}%`;
    if (color) span.style.color = color;
    els.floatLayer.appendChild(span);
    setTimeout(() => span.remove(), 950);
  }

  function tossAnim() {
    els.wok.classList.remove("tossing");
    void els.wok.offsetWidth;
    els.wok.classList.add("tossing");
  }

  function shake() {
    els.wokZone.classList.remove("shake");
    void els.wokZone.offsetWidth;
    els.wokZone.classList.add("shake");
  }

  /* ---- canvas FX ---- */
  function resizeCanvas() {
    const rect = els.wokZone.getBoundingClientRect();
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    els.canvas.width = Math.max(1, Math.floor(rect.width * dpr));
    els.canvas.height = Math.max(1, Math.floor(rect.height * dpr));
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function spawnBurst(n, golden) {
    const rect = els.wokZone.getBoundingClientRect();
    const cx = rect.width * 0.5;
    const cy = rect.height * 0.52;
    for (let i = 0; i < n; i++) {
      const a = Math.random() * Math.PI * 2;
      const sp = 2 + Math.random() * (golden ? 7 : 4);
      particles.push({
        x: cx + (Math.random() - 0.5) * 40,
        y: cy + (Math.random() - 0.5) * 20,
        vx: Math.cos(a) * sp,
        vy: Math.sin(a) * sp - (golden ? 3 : 1),
        life: 1,
        decay: 0.015 + Math.random() * 0.02,
        r: 2 + Math.random() * 3.5,
        color: golden
          ? ["#e8b84b", "#f5d76e", "#ff7a3d", "#fff3c4"][(Math.random() * 4) | 0]
          : ["#f0d48a", "#e89b4b", "#7cb87c", "#f5f0e6"][(Math.random() * 4) | 0],
        rot: Math.random() * Math.PI,
        vr: (Math.random() - 0.5) * 0.3,
      });
    }
  }

  function spawnSteam() {
    const rect = els.wokZone.getBoundingClientRect();
    particles.push({
      x: rect.width * 0.5 + (Math.random() - 0.5) * 60,
      y: rect.height * 0.42,
      vx: (Math.random() - 0.5) * 0.4,
      vy: -0.6 - Math.random() * 0.7,
      life: 1,
      decay: 0.012 + Math.random() * 0.01,
      r: 8 + Math.random() * 14,
      color: "rgba(255,255,255,0.35)",
      steam: true,
      rot: 0,
      vr: 0,
    });
  }

  function drawFX() {
    if (!ctx) return;
    const w = els.canvas.clientWidth;
    const h = els.canvas.clientHeight;
    ctx.clearRect(0, 0, w, h);

    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      if (!p.steam) p.vy += 0.12;
      p.life -= p.decay;
      p.rot += p.vr;
      if (p.life <= 0) {
        particles.splice(i, 1);
        continue;
      }
      ctx.save();
      ctx.globalAlpha = Math.max(0, p.life);
      ctx.translate(p.x, p.y);
      ctx.rotate(p.rot);
      if (p.steam) {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(0, 0, p.r * (1.5 - p.life * 0.5), 0, Math.PI * 2);
        ctx.fill();
      } else {
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.ellipse(0, 0, p.r * 1.4, p.r * 0.9, 0, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }
  }

  /* ---- step flow ---- */
  function resetGame() {
    state.running = false;
    state.stepIndex = 0;
    state.tossHit = 0;
    state.score = 0;
    state.combo = 0;
    state.maxCombo = 0;
    state.perfect = 0;
    state.good = 0;
    state.miss = 0;
    state.heat = 18;
    state.awaitingInput = false;
    particles.length = 0;
    els.wokFood.classList.remove("filled", "burnt");
    els.wokFlame.classList.remove("on");
    els.tossPips.hidden = true;
    els.tossPips.innerHTML = "";
    updateHUD();
    updateRecipe();
  }

  function startGame() {
    resetGame();
    buildRecipe();
    showScreen("game");
    setDialogue(rand(LINES.start));
    setCharMood(null);
    resizeCanvas();
    state.running = true;
    beginStep();
  }

  function beginStep() {
    if (state.stepIndex >= STEPS.length) {
      finishGame();
      return;
    }
    const step = STEPS[state.stepIndex];
    state.tossHit = 0;
    state.awaitingInput = true;
    state.lastT = performance.now();

    els.hudStepIndex.textContent = String(state.stepIndex + 1);
    els.hudStepName.textContent = step.name;
    els.timingHint.textContent =
      step.type === "toss"
        ? `连续 ${step.tossCount} 次完美颠勺！每次指针进绿区就按`
        : `${step.icon} ${step.name}：指针进入金色中心得「完美」`;

    // toss pips
    if (step.type === "toss") {
      els.tossPips.hidden = false;
      els.tossPips.innerHTML = "";
      for (let i = 0; i < step.tossCount; i++) {
        const d = document.createElement("span");
        d.className = "pip";
        els.tossPips.appendChild(d);
      }
      els.wokFlame.classList.add("on");
      setDialogue("大火翻炒！跟着节拍连续颠起来！");
    } else {
      els.tossPips.hidden = true;
      if (step.name.includes("出锅")) setDialogue(rand(LINES.done));
      else if (state.heat >= 80 && Math.random() > 0.5) setDialogue(rand(LINES.hot));
    }

    // food visual fills as we progress
    if (state.stepIndex >= 2) els.wokFood.classList.add("filled");
    if (state.heat >= 90) els.wokFood.classList.add("burnt");
    else els.wokFood.classList.remove("burnt");

    layoutZones();
    updateRecipe();
    updateHUD();

    if (!state.raf) state.raf = requestAnimationFrame(tick);
  }

  function hit() {
    if (!state.running || !state.awaitingInput) return;
    const step = STEPS[state.stepIndex];
    const dist = Math.abs(state.markerPos - state.zoneCenter);
    let kind;
    if (dist <= state.perfectW / 2) kind = "perfect";
    else if (dist <= state.goodW / 2) kind = "good";
    else kind = "miss";

    applyJudgment(kind, step);
  }

  function applyJudgment(kind, step) {
    if (kind === "perfect") {
      state.combo += 1;
      state.perfect += 1;
      const gain = Math.round(100 * (1 + Math.min(state.combo, 20) * 0.1));
      state.score += gain;
      state.heat = Math.min(100, state.heat + step.heat * 0.7);
      showJudge("perfect");
      floatText(`+${gain}`, "#e8b84b");
      setCharMood("cheer");
      if (Math.random() > 0.4) setDialogue(rand(LINES.perfect));
      if (step.type === "toss") {
        spawnBurst(28, true);
        shake();
      } else {
        spawnBurst(14, false);
      }
      tossAnim();
      advanceHit(true);
    } else if (kind === "good") {
      state.combo += 1;
      state.good += 1;
      const gain = Math.round(50 * (1 + Math.min(state.combo, 20) * 0.05));
      state.score += gain;
      state.heat = Math.min(100, state.heat + step.heat * 0.45);
      showJudge("good");
      floatText(`+${gain}`, "#7cb87c");
      setCharMood("cheer");
      if (Math.random() > 0.5) setDialogue(rand(LINES.good));
      spawnBurst(8, false);
      tossAnim();
      advanceHit(true);
    } else {
      state.combo = 0;
      state.miss += 1;
      state.heat = Math.min(100, state.heat + 4);
      showJudge("miss");
      setCharMood("dismay");
      setDialogue(rand(LINES.miss));
      spawnBurst(6, false);
      advanceHit(false);
    }
    state.maxCombo = Math.max(state.maxCombo, state.combo);
    updateHUD();
  }

  function advanceHit(success) {
    const step = STEPS[state.stepIndex];
    if (step.type === "toss") {
      if (success) {
        state.tossHit += 1;
        const pips = els.tossPips.children;
        if (pips[state.tossHit - 1]) pips[state.tossHit - 1].classList.add("on");
      }
      // miss on toss: require restart of this pip count? softer: still need full count
      if (state.tossHit >= step.tossCount) {
        completeStep();
      } else {
        // re-arm with slightly faster marker
        state.markerSpeed = step.speed * 1.08;
        state.markerPos = state.markerPos > 0.5 ? 0.04 : 0.96;
        state.markerDir = state.markerPos < 0.5 ? 1 : -1;
        layoutZoneOnly();
        state.awaitingInput = true;
      }
    } else {
      completeStep();
    }
  }

  function layoutZoneOnly() {
    const step = STEPS[state.stepIndex];
    state.goodW = step.good;
    state.perfectW = step.perfect;
    // keep same zone center for multi-toss consistency within step
    const trackW = els.timingTrack.clientWidth || 400;
    const goodPx = state.goodW * trackW;
    const perfectPx = state.perfectW * trackW;
    const centerPx = state.zoneCenter * trackW;
    els.zoneGood.style.left = `${centerPx - goodPx / 2}px`;
    els.zoneGood.style.width = `${goodPx}px`;
    els.zonePerfect.style.left = `${centerPx - perfectPx / 2}px`;
    els.zonePerfect.style.width = `${perfectPx}px`;
  }

  function completeStep() {
    state.awaitingInput = false;
    const step = STEPS[state.stepIndex];
    if (step.heat > 0 && step.type === "toss") {
      state.heat = Math.min(100, state.heat + step.heat * 0.3);
      els.wokFlame.classList.add("on");
    }
    updateHUD();
    updateRecipe();

    // brief settle then next
    clearTimeout(state.settleTimer);
    state.settleTimer = setTimeout(() => {
      state.stepIndex += 1;
      if (state.stepIndex >= STEPS.length) {
        els.wokFlame.classList.remove("on");
        finishGame();
      } else {
        beginStep();
      }
    }, 420);
  }

  function autoMiss() {
    if (!state.awaitingInput) return;
    const step = STEPS[state.stepIndex];
    applyJudgment("miss", step);
    // for non-toss, advanceHit already completes; for toss need to still progress attempts
    if (step.type === "toss" && state.tossHit < step.tossCount) {
      // force count attempt: soft fail still leaves pips; after 2 autos misses, bail step
      // keep trying until complete — increase speed slightly
      state.markerSpeed *= 1.05;
    }
  }

  function finishGame() {
    state.running = false;
    state.awaitingInput = false;
    cancelAnimationFrame(state.raf);
    state.raf = 0;
    clearTimeout(state.settleTimer);

    // heat decay cosmetic finish
    const total = STEPS.length;
    const ratio = state.perfect / total;
    let stars, title, key;
    if (ratio >= 0.85 && state.miss <= 1) {
      stars = 3; title = "传说级出餐"; key = "s";
    } else if (ratio >= 0.55 && state.miss <= 4) {
      stars = 2; title = "美味出餐"; key = "a";
    } else if (state.perfect + state.good >= Math.ceil(total * 0.5)) {
      stars = 1; title = "勉强出餐"; key = "b";
    } else {
      stars = 1; title = "黑暗料理…"; key = "c";
      if (state.perfect + state.good < 3) stars = 1;
    }
    // recompute stars more gently for c
    if (key === "c") stars = 0;
    if (key === "b") stars = 1;
    if (key === "a") stars = 2;
    if (key === "s") stars = 3;

    els.resultTitle.textContent = title;
    els.resultScore.textContent = String(state.score);
    els.resultCombo.textContent = String(state.maxCombo);
    els.resultPerfect.textContent = String(state.perfect);
    els.resultMiss.textContent = String(state.miss);
    els.resultComment.textContent = RESULT_COMMENTS[key];
    els.resultStars.innerHTML = [0, 1, 2]
      .map((i) => `<span class="${i < stars ? "" : "dim"}">★</span>`)
      .join("");

    showScreen("result");
  }

  /* ---- loop ---- */
  function tick(now) {
    state.raf = requestAnimationFrame(tick);
    const dt = Math.min(0.05, (now - (state.lastT || now)) / 1000);
    state.lastT = now;

    if (state.running && state.awaitingInput) {
      state.markerPos += state.markerDir * state.markerSpeed * dt;
      if (state.markerPos >= 1) {
        state.markerPos = 1;
        state.markerDir = -1;
        // one full pass without input = miss
        autoMiss();
      } else if (state.markerPos <= 0) {
        state.markerPos = 0;
        state.markerDir = 1;
        autoMiss();
      }
      els.marker.style.left = `${state.markerPos * 100}%`;
    }

    // heat ambient decay / rise visuals
    if (state.running) {
      const step = STEPS[state.stepIndex];
      if (step && step.type === "toss") {
        state.heat = Math.min(100, state.heat + 3.5 * dt);
      } else {
        state.heat = Math.max(12, state.heat - 2.5 * dt);
      }
      els.heatFill.style.width = `${state.heat}%`;
      els.heatBar.classList.toggle("hot", state.heat >= 85);

      if (els.wokFood.classList.contains("filled")) {
        if (Math.random() < 0.06) spawnSteam();
      }
    }

    drawFX();
  }

  /* ---- input ---- */
  function onPressHit(e) {
    if (e) e.preventDefault();
    els.btnHit.classList.add("pressed");
    setTimeout(() => els.btnHit.classList.remove("pressed"), 90);
    if (els.screens.game.classList.contains("active") && state.running) hit();
  }

  els.btnHit.addEventListener("click", onPressHit);
  window.addEventListener("keydown", (e) => {
    if (e.code === "Space" || e.key === " ") {
      if (els.screens.game.classList.contains("active")) {
        e.preventDefault();
        onPressHit(e);
      } else if (els.screens.title.classList.contains("active")) {
        e.preventDefault();
        startGame();
      }
    }
  });

  // click anywhere on game stage (except buttons) also hits
  els.wokZone.addEventListener("pointerdown", () => {
    if (state.running) hit();
  });

  els.btnStart.addEventListener("click", startGame);
  els.btnRetry.addEventListener("click", startGame);

  els.btnHome.addEventListener("click", () => {
    state.running = false;
    cancelAnimationFrame(state.raf);
    state.raf = 0;
    showScreen("title");
  });

  window.addEventListener("resize", () => {
    if (els.screens.game.classList.contains("active")) {
      resizeCanvas();
      if (state.running && state.awaitingInput) layoutZoneOnly();
    }
  });

  // boot
  buildRecipe();
  ctx = els.canvas.getContext("2d");
  resizeCanvas();
  state.lastT = performance.now();
  state.raf = requestAnimationFrame(tick);
  showScreen("title");
})();
