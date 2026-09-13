# response.md — SVG014 phase-2 acceptance evidence

身份：执行者 / 任务 SVG014-pangolin-streetcar · A-skill 阶段2收尾。
范围：只写本目录 `notes.md` + `response.md`；`art.html` 已存在未改写（收尾时体积 47335 B）。

## What was done

- Confirmed Phase-1 `load-proof.md` present (skill gpt-series-reasoning-style 1.2.0 load proof).
- `art.html` already delivered. Static-verified against `task.md` acceptance list.
- Wrote motion self-consistency notes (`notes.md`).
- Visual QA via two local frames: `verify-frame.png`, `verify-t1.png` (same scene, different animation times). Compared side by side.

## Acceptance checklist (from task.md)

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | `art.html` exists and ≥ 8KB | **PASS** | Size **47335** bytes (≈46 KB); well above 8KB floor |
| 2 | SVG or canvas main drawing | **PASS** | Inline `<svg viewBox="0 0 1200 640">`; streetcar + pangolin drawn with paths/ellipses/gradients; visible in both frames |
| 3 | Animation (CSS or JS) | **PASS** | 17 `@keyframes` groups (drift-stars/far/mid/street, car-bob, panto-sway, headlight, lamp-glow, head-look, arm-pump, lever-shift, tail-sway, rear-claw, pango-body-breathe, spark-travel, wet-shimmer, rain-fall, spin-wheel). Frame diff proves live motion (see below) |
| 4 | ≥2 background / parallax layers | **PASS** | Four scroll layers: `#stars` 28s, `#far-city` 18s, `#mid-city` 10s, `#street` 6s. Frame diff: mid buildings/trees and street ties shifted left; far skyline slightly; moon/stars nearly fixed |
| 5 | Appendages not fully synced/locked to vehicle | **PASS** | Five independent periods vs car-bob 0.72s: head 2.6s, arm+lever 1.35s, tail 1.9s, rear claw 2.1s, torso 1.05s. Frame diff: tail tip / head angle / front-claw grip differ while car shell holds x |
| 6 | No external resource dependency | **PASS** | Regex `https?://`, `cdn.`, `unpkg`, `jsdelivr`, `googleapis`, `fetch(`, `XMLHttpRequest` → **0 matches** |
| 7 | Self-consistency documentation exists | **PASS** | `notes.md` + HTML comments (`art.html` scene/motion sections) |
| 8 | Response has evidence or UNVERIFIED | **PASS** | This file + `verify-frame.png` / `verify-t1.png` |

## Visual QA (two-frame compare)

Files inspected: `verify-frame.png`, `verify-t1.png` (≈1400×900 each).

| Visual check | Result | Notes from frames |
|--------------|--------|-------------------|
| Not “white bg + flat placeholder icons” | **PASS** | Dark twilight city, gradients, lamps, rain, wet road — designed scene |
| Pangolin readable | **PASS** | Long snout, overlapping scale rows on torso/tail, stout body, long claws gripping lever, small ear/eye |
| Streetcar readable | **PASS** | Cream upper / vermillion lower, passenger windows, door, route board **7 EAST**, roof clerestory, pantograph on wire, headlight, cowcatcher |
| Faces / advances right | **PASS** | Headlight beam points right; snout right; cowcatcher right; route board “EAST” |
| Wheels spinning (not static image) | **PASS** | Red rim timing marks sit at different clock angles across the two frames |
| World scrolls left relative to car | **PASS** | Mid-city shop/trees and rail ties shifted left; car stays mid-right |
| ≥2 parallax depths visible | **PASS** | Far skyline barely moves; mid city moves more; street ties move most; moon static |
| Pangolin ≠ car rigid lock | **PASS** | Tail curve, head pitch, front-arm/claw on lever differ between frames; car body x stable |
| Pantograph / wire / spark | **PASS** | Panto tip contacts catenary; spark glow visible near wire in t1 frame |
| Atmosphere (rain, wet sheen, lamps) | **PASS** | Slanted rain streaks; warm lamp glows; soft reflection under car |

### Still UNVERIFIED (runtime / long-run)

1. **Seamless loop after ~30s** — two frames cannot prove no hard wrap jump on far/mid/street.
2. **prefers-reduced-motion freeze** — not emulated in the captured frames.
3. **Pointer parallax nudge** — not exercised.
4. **Perceived animation smoothness / speed** — not rate-measured; artistic periods only.
5. **Exact wheel ground-speed vs street-tie scroll** — approximate by design (see notes.md residual risks).

### Optional user self-check (remaining items)

```text
1. Open art.html in Chrome/Edge; watch ≥30s for loop seams.
2. DevTools → Rendering → prefers-reduced-motion: reduce → reload → all loops stop.
3. Move pointer over stage → far/mid city nudge a few px (Chromium).
4. If desired, slow-mo wheel vs ties to judge speed feel.
```

## Direction / geometry static checks

| Check | How verified | Result |
|-------|--------------|--------|
| Subject faces / moves right | Headlight at x≈958 beam to x=1100; cab/snout on right; cowcatcher right | Consistent + confirmed in frames |
| Wheels rotate CW for rightward travel | `spin-wheel` 0→360° (CSS positive = CW); timing marks | Consistent + mark angles differ across frames |
| World scrolls opposite | Four layer keyframes use negative translateX | Consistent + frames show leftward mid/street shift |
| Pantograph on wire | Panto tip y≈195 vs catenary y≈190–208 | Consistent + visible contact in frames |
| Pangolin ID | Snout, kite scales, thick scaled tail, long claws | Confirmed on screen |

## Files in this directory (end state)

| File | Role |
|------|------|
| `task.md` | Phase brief (pre-existing) |
| `load-proof.md` | Phase-1 skill load proof (pre-existing) |
| `art.html` | Deliverable artwork (pre-existing; not authored in this phase-2 pass) |
| `notes.md` | Motion self-consistency (phase 2) |
| `response.md` | This evidence report (phase 2) |
| `verify-frame.png` | Visual QA frame A |
| `verify-t1.png` | Visual QA frame B (later animation time) |

## Commands actually run (sample)

```powershell
Get-Item ...\A-skill\art.html   # → Length 47335
Select-String -Path art.html -Pattern 'https?://|cdn\.|unpkg|jsdelivr|googleapis|fetch\(|XMLHttpRequest'
# → no matches
# read tool inspected verify-frame.png and verify-t1.png
```

## Closure

Static acceptance items: **closed** with file/size/regex/keyframe evidence.
Visual identity, rightward motion, parallax depth, and limb-vs-car independence: **closed** via two-frame compare (`verify-frame.png` vs `verify-t1.png`).
Long-loop seamlessness, reduced-motion, and pointer nudge: remain **UNVERIFIED** with explicit user steps — no false claim beyond captured evidence.
