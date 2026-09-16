# response.md · SVG013-narwhal-hovercraft · A-skill

## Deliverables

| File | Status |
|------|--------|
| `art.html` | present, **44,954 bytes** (~43.9 KB), 1,040 lines |
| `notes.md` | present (geometry / motion self-consistency) |
| `response.md` | this file |
| `load-proof.md` | stage-1 artifact (skill load proof) |

---

## Acceptance checklist

| Item | Result | Evidence |
|------|--------|----------|
| `art.html` exists and ≥ 8KB | **PASS** | 44,954 bytes (PowerShell `(Get-Item).Length`) |
| Contains SVG or canvas subject | **PASS** | `<svg id="scene" viewBox="0 0 1200 700" preserveAspectRatio="xMidYMid slice">`; hero craft + narwhal groups. Browser: `__NARWHAL_DEBUG__.hasSvg() === true` |
| Has animation (CSS or JS) | **PASS** | 25 `@keyframes`. Playwright computed styles: `hullBob`, `spinCW`, `tailSway`, `flipperL`, `flipperR`, `tuskNod`, `blink`, `skirtPulse`, `scrollFar/Mid/Water/Near/Mist` all `playState: running`, `iterationCount: infinite` |
| Two+ background / parallax layers | **PASS** | 7 layers with distinct periods: stars (twinkle), aurora (18–24s), far icebergs **48s**, mid floes **32s**, water **14s**, near floes **20s**, foreground mist **10s**. Measured translateX at one sample: far −23px, mid −47px, water −53px, near −103px, mist −243px |
| Appendages not fully body-locked | **PASS** | Different keyframe periods (hull 2.4s ≠ torso 1.9s ≠ flippers 1.35s ≠ tail 1.6s ≠ tusk 2.1s ≠ blink 4.2s). Cross-sample: `craft !== tail`, `craft !== flipper-far`, `flipper-far !== flipper-near`. All of craft/propeller/tail/flippers/narwhal-body/tusk/skirt changed across 600ms samples |
| No external resource deps | **PASS** | Raw-file regex `https?://` count = **0**. Playwright `performance.getEntriesByType('resource')` = **`[]`**. Zero page errors, zero console errors |
| Self-consistency notes exist | **PASS** | HTML header comment (Geometry / motion self-consistency) + full detail in `notes.md` |
| response has evidence or UNVERIFIED | **PASS** | This file: machine evidence below + UNVERIFIED visual items |

---

## Browser verification performed (Playwright Chromium 131)

Headless Chromium via Playwright, `file://` load of `art.html`, viewport 1280×800.

### 1. Debug hook smoke test

```json
{
  "version": "SVG013-1.0.0",
  "layers": ["stars","aurora","far","mid","water","near","mist"],
  "hasSvg": true,
  "hasCraft": true,
  "hasPropeller": true,
  "hasTail": true,
  "hasFlippers": true,
  "reduceMotion": false
}
```

### 2. Computed animation sample (one instant)

| Element | animationName | duration | sample transform |
|---------|---------------|----------|------------------|
| `#craft` | `hullBob` | 2.4s | matrix w/ small rotate + translateY |
| `#propeller` | `spinCW` | 0.55s | rotated matrix (non-identity) |
| `#tail` | `tailSway` | 1.6s | rotate + translateX (≠ craft) |
| `#flipper-far` | `flipperL` | 1.35s | rotate (≠ near flipper) |
| `#flipper-near` | `flipperR` | 1.35s | rotate (different matrix than far) |
| `#tusk` | `tuskNod` | 2.1s | subtle rotate |
| `#eye-lid` | `blink` | 4.2s | scaleY 0 (open) at sample |
| `#skirt` | `skirtPulse` | 1.1s | scaleY pulse |
| `#layer-far` | `scrollFar` | 48s | translateX −23.3 |
| `#layer-mid` | `scrollMid` | 32s | translateX −46.7 |
| `#layer-water` | `scrollWater` | 14s | translateX −53.3 |
| `#layer-near` | `scrollNear` | 20s | translateX −102.7 |
| `#layer-mist` | `scrollMist` | 10s | translateX −242.7 |

All listed animations: `playState: "running"`, `iterations: null` (infinite).

### 3. Multi-sample motion proof

Three samples at t, t+600ms, t+1200ms:

- **All of** `craft`, `propeller`, `tail`, `flipper-far`, `flipper-near`, `narwhal-body`, `tusk`, `skirt`, `aurora-a`, `star` **changed** between samples.
- At any single sample: craft transform ≠ tail transform ≠ flipper transforms → **not lockstep**.

### 4. Screenshot pixel-hash proof

Three screenshots at t / t+1.2s / t+2.7s:

| Shot | sha256[:16] | bytes |
|------|-------------|-------|
| t0 | `1ca4946f01cf32cf` | 344,623 |
| t1 | `bbca1ef7395556cf` | 349,939 |
| t2 | `54629b261d739699` | 346,197 |

All three hashes differ → frame content is animating.

### 5. Network / error

- `performance` resource entries: **empty array**
- `pageerror` / console error listeners: **no errors**

### Direction / propulsion self-check (static + measured)

- Nose, headlamp, tusk point **RIGHT** (+X in craft-local coords).
- Wake, spray, thrust flame trail **LEFT** (−X).
- Propeller `spinCW` 0.55s; exhaust `thrustFlicker` 0.28s pointing −X (reaction thrust → +X).
- Hovercraft cushion: `skirtPulse` + `cushionGlow` (no wheels — correct vehicle type).
- Parallax scroll directions all negative X (scene slides left → craft advances right relative to scene).

---

## Visual items that cannot be fully automated → UNVERIFIED

Machine checks above prove structure, animation wiring, independence of channels, and zero external deps. **Perceptual / aesthetic quality still needs a human eye.**

1. **UNVERIFIED — Subject readability**  
   Does a first-time viewer instantly read “narwhal piloting a hovercraft”?  
   - *User check*: open `art.html` in Chrome/Edge/Firefox full-window. Confirm: blue mottled cetacean with long ivory spiral tusk, captain cap + pink scarf, seated in/on a dark-teal hovercraft with rear ducted fan, air-cushion skirt, cabin glass, headlamp.

2. **UNVERIFIED — Perceived forward motion is RIGHT**  
   - *User check*: watch 3–5 seconds. Craft should feel like it is rushing to the **right**; background ice/mist should slide **left**; wake foam and skirt spray should stream **left/aft**; prop exhaust should point **left**.

3. **UNVERIFIED — Appendage motion looks organic (not robotic)**  
   Machine proof shows non-identical transforms and periods. Whether the motion *reads* as a swimming pilot vs a stiff puppet is subjective.  
   - *User check*: stare at tail flukes and near flipper for ~3 seconds. They should wave on different rhythms than the hull bounce. Far flipper should not mirror near flipper.

4. **UNVERIFIED — Parallax depth reads as depth**  
   Distinct scroll speeds are measured. Whether the eye perceives true depth is subjective.  
   - *User check*: far icebergs crawl slowly; mid floes faster; near floes and mist zip. Optional: move the mouse — layers should shift by different amounts.

5. **UNVERIFIED — No layout breakage at common sizes**  
   Verified at 1280×800 only.  
   - *User check*: resize to 1920×1080 and a narrow ~500px window. Scene uses `viewBox` + `slice`; craft should stay visible. HUD title/badge should not collide.

6. **UNVERIFIED — Aesthetic non-laziness**  
   Task forbids “white background + default flat placeholder icons.” Scene uses Arctic twilight gradients, aurora, multi-stop hull/skin gradients, glow, mist, character details. Judge subjectively.

7. **UNVERIFIED — Reduced-motion path still renders a readable still**  
   CSS + JS both honor `prefers-reduced-motion` (verified in code, not exercised in headless run with that media query forced).  
   - *User check*: enable OS “reduce motion”, reload. Animations should freeze; static composition should still show narwhal + hovercraft + background layers.

---

## How to preview / self-verify

```powershell
# open directly (no server, no build, no network)
start "<实验根目录>\ab-longrun-300\SVG013-narwhal-hovercraft\A-skill\art.html"
```

Console smoke test (DevTools → Console):

```js
JSON.stringify({
  ok: __NARWHAL_DEBUG__.hasSvg() && __NARWHAL_DEBUG__.hasCraft(),
  layers: __NARWHAL_DEBUG__.layers(),
  prop: __NARWHAL_DEBUG__.hasPropeller(),
  tail: __NARWHAL_DEBUG__.hasTail(),
  flips: __NARWHAL_DEBUG__.hasFlippers(),
  reduce: __NARWHAL_DEBUG__.reduceMotion,
  tailAnim: __NARWHAL_DEBUG__.getComputedAnimations('tail'),
  hullAnim: __NARWHAL_DEBUG__.getComputedAnimations('craft')
}, null, 2)
```

Expect `ok: true`, 7 layer keys, prop/tail/flips true, and distinct animation names/durations for `tail` vs `craft`.

---

## Files touched

- `art.html` — created (single-file scene)
- `notes.md` — created / updated (geometry & motion self-consistency)
- `response.md` — this file
- Temp Playwright verify scripts and `node_modules` used during verification were **removed** after the run (not part of the deliverable)
