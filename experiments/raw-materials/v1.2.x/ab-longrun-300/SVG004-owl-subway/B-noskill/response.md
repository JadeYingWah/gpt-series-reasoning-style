# SVG004-owl-subway · Response (B-noskill)

## Deliverables

| File | Status |
|---|---|
| `art.html` | Delivered — 48,914 bytes (≥ 8 KB) |
| `notes.md` | Delivered — geometry / motion coherence notes |
| `response.md` | This file |

## Acceptance checklist

| Item | Result | Evidence |
|---|---|---|
| `art.html` exists and ≥ 8 KB | **PASS** | File length 48,914 bytes (PowerShell `Get-Item` / `Get-Content -Raw`) |
| Contains SVG or canvas body | **PASS** | `<svg class="scene" viewBox="0 1280x720">` present; full scene is SVG |
| Has animation (CSS or JS) | **PASS** | 16 `@keyframes` blocks, multiple SMIL `<animate>`, plus a `requestAnimationFrame` parallax loop |
| ≥ 2 layers background / parallax | **PASS** | 4 depth cues: `layer-far` (depth 0.05), `layer-mid` (0.18), `layer-near` (0.55), plus CSS speed streaks |
| Appendages not fully synced to vehicle | **PASS** | Owl has 5 independent DOFs vs train body (see below) |
| No external resource dependencies | **PASS** | Only `http` match is `xmlns="http://www.w3.org/2000/svg"` (namespace URI, not a fetch). No CDN / framework / network requests. |
| Coherence notes exist | **PASS** | HTML comment block inside `art.html` + full `notes.md` |
| Response has evidence or UNVERIFIED | **PASS** | This file |

## Owl appendage independence (automated DOM checks)

Exposed on `window.__OWL_SUBWAY_CHECKS__` at runtime; static source counts:

| Selector | Source occurrences | Role |
|---|---|---|
| `.wheel-spin` | 6 | Wheel groups (forward = CW) |
| `.owl-head` | 3 | Head bob/rotate, 1.6 s |
| `.owl-wing-l` / `.owl-wing-r` | 6 | Independent wing flaps, 0.7 s |
| `.owl-tail` | 3 | Tail twitch, 1.1 s |
| `.owl-claw` | 2 | Claw grip on lever, 0.9 s |
| `data-depth` | 4 | Far / mid / near + streak group |
| `class="sleepers"` | 1 | Rail-tie scroll, 0.55 s / 80 px |
| `class="streak"` | 6 | Speed lines |

Train body only has a ±1.5 px suspension bounce at 0.55 s. Owl head, wings,
tail, and claw all run on **different periods** than the train bounce, so the
owl is not body-locked.

## Forward-direction coherence (checked in source)

- Nose / windshield / headlight / bumper are on the **right** (+X).
- Wheels use `animation: spin-cw` (clockwise) so contact patch moves −X
  relative to the train — correct for rightward travel.
- Sleepers translate −80 px per 0.55 s, same period as one wheel revolution.
- Exhaust puffs and speed streaks drift −X.
- Owl pupils are offset toward +X (looking ahead).

## UNVERIFIED (visual / subjective — user check)

These cannot be fully automated from a headless text check. Open `art.html`
in a browser and confirm:

1. **Owl is clearly recognizable** as a bird (ear tufts, facial disc, big
   yellow eyes, beak, feathered wings) rather than a generic blob.
   → *Self-check: look at the front cab windshield. You should see a
   brown/tan owl with two ear tufts and large yellow eyes.*
2. **Subway is clearly recognizable** as a train (car body, blue livery
   band, passenger windows, door, bogies, rails, destination board
   "NIGHT OWL", route badge "OWL-7").
   → *Self-check: the vehicle should read as a metro car sitting on
   double rails, not a bus or truck.*
3. **Wheel rotation visually matches rightward travel** (not spinning
   backwards).
   → *Self-check: watch the white triangular notch on each wheel. As the
   train faces right, the notch at the top of the wheel should move to
   the right (clockwise).*
4. **Owl limbs visibly move relative to the cabin** (head bobs, wings
   flap, tail twitches) while the train only micro-bounces.
   → *Self-check: stare at the owl for ~3 seconds. Head tilt and wing
   flap should be obvious and out of phase with each other.*
5. **Parallax depth reads correctly** — distant skyline barely moves,
   mid buildings move moderately, track/sleepers move fastest.
   → *Self-check: move the mouse left/right across the stage. Far layer
   should barely shift; near track should shift more. Sleepers should
   also scroll left continuously on their own.*
6. **No "white background + flat placeholder icon" look.**
   → *Self-check: the page should be a dark night-city scene with
   gradients, glows, and hand-drawn geometry.*
7. **Motion is smooth** (no jank / popping loops).
   → *Self-check: watch for 10+ seconds. Sleepers and wheels should loop
   without a visible jump.*

## How to open

Open `art.html` in any modern browser (Edge / Chrome / Firefox). No build
step, no server required. Works offline.

## Arm note

B-noskill: no skill files were loaded. All design and implementation were
done directly from `task.md`.
