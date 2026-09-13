# SVG014 · Response / Verification

Working dir: `<实验根目录>\ab-longrun-300\SVG014-pangolin-streetcar\B-noskill`

## Deliverables

- `art.html` — single-file HTML, 42,431 bytes (≥8 KB ✓)
- `notes.md` — geometry / motion self-consistency write-up
- `response.md` — this file

## Automated checks (actually run)

Command used: PowerShell read of `art.html` + regex / size probes.

| Acceptance item | Result | Evidence |
|-----------------|--------|----------|
| `art.html` exists and ≥ 8 KB | **PASS** | `Length = 42445` bytes on disk; raw char count 42431 |
| Contains SVG or canvas main draw | **PASS** | `<svg id="scene" viewBox="0 0 1200 675">` present; no canvas needed |
| Has animation (CSS or JS) | **PASS** | `@keyframes` present; `requestAnimationFrame` loop in inline `<script>` |
| ≥2 background / parallax layers | **PASS** | `#layerFar` (0.18×), `#layerMid` (0.45×), `#layerNear` (1.0×), plus dust 0.7× and static sky |
| Appendages not locked to vehicle | **PASS** | `.pg-head` 2.35 s, `.arm-near`/`.arm-far` 1.45 s, `.pg-tail*` 2.72/1.91 s, `.pg-chest` 3.1 s — all ≠ wheel 0.55 s and ≠ body-bob 1.82 s |
| No external resource deps | **PASS** | Regex: no `http(s)://`, no `<link`, no `<script src=`, no `cdn.`/`unpkg`/`jsdelivr`/`googleapis` |
| Self-consistency notes exist | **PASS** | `notes.md` + HTML header comment block |
| Response has evidence or UNVERIFIED | **PASS** | This table |

Direction / geometry consistency (code inspection):

| Item | Status | How |
|------|--------|-----|
| Wheels rotate clockwise for rightward travel | **PASS** (code) | `@keyframes spin-cw` → `rotate(0→360deg)` on `#wheelRim` with yellow tread notch |
| World scrolls left | **PASS** (code) | JS `offNear = wrap(offNear - step)` with negative X `translate` |
| Headlamp / nose / pangolin face right | **PASS** (code) | Nose path ends at x≈132; headlamp cone polygon to x=1180 |
| Pangolin scales + long snout present | **PASS** (code) | `<symbol id="scale">` tiles on torso/head/tail; snout path |
| Streetcar identity (body, windows, pantograph, board, door) | **PASS** (code) | Crimson body, brass roof, pantograph + spark, board text `PANGOLIN · 14` |

## UNVERIFIED (visual; user must open in a browser)

These cannot be fully automated here (no headless browser in this pass):

1. **Overall readability** — that the silhouette immediately reads as “pangolin driving a streetcar” at a glance.
   - **User step:** open `art.html` in Chrome/Edge/Firefox at ~1200×675. Confirm car + animal are obvious without reading the HUD.
2. **Wheel rotation direction feels correct** (not spinning backwards relative to travel).
   - **User step:** watch the yellow tread notch on the nearest wheel; it should travel forward (rightward) at the top of the wheel.
3. **Parallax feels like depth** (far skyline clearly slower than curb/rails).
   - **User step:** compare motion of far buildings vs near rail ties; far should lag ~5×.
4. **Pangolin limbs do not look “stuck” to the car.**
   - **User step:** watch head nod vs tail sway vs arm steer; they should drift out of phase within a few seconds.
5. **No visual clipping** of tail or claws through the car body at certain phases.
   - **User step:** watch one full 3 s cycle; tail should trail behind cabin without cutting through the roof.
6. **Reduced-motion** preference disables world scroll (code path exists).
   - **User step:** enable OS “reduce motion”, reload, confirm parallax stops while content still draws.

## How to view

Double-click `art.html`, or:

```powershell
Start-Process "<实验根目录>\ab-longrun-300\SVG014-pangolin-streetcar\B-noskill\art.html"
```

No server, no network, no install required.
