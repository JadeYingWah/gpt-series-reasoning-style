# notes.md · SVG013-narwhal-hovercraft · Geometry & Motion Self-Consistency

Single-file deliverable: `art.html` (inline CSS + JS, no CDN/network).
Scene title: *Narwhal Courier · Arctic Hover Express*.

---

## 1. Forward direction (canonical)

| Cue | Setting |
|-----|---------|
| Craft nose / headlamp / tusk | point **RIGHT** (+X) |
| Stern thruster / wake / spray | trail **LEFT** (−X) |
| Parallax scroll | all layers `translateX` **negative** → scene slides left → craft advances right relative to scene |
| Speed lines | animate from nose forward, then fade left |

Craft local comment (HTML): *“Craft faces RIGHT. Nose at +X, thruster at −X.”*

---

## 2. Vehicle type: hovercraft (no wheels/tracks)

This is an **air-cushion hovercraft**, not a wheeled vehicle. Task item “wheel/track/propeller cycle matches forward direction” is satisfied via:

| Channel | Animation | Period | Role |
|---------|-----------|--------|------|
| Ducted propeller | `spinCW` 0→360° | **0.55 s** | rear thrust; blades rotate CW (viewed from starboard) so thrust drives craft +X |
| Thrust flame | `thrustFlicker` scaleX/opacity | **0.28 s** | exhaust points −X (reaction → +X) |
| Skirt | `skirtPulse` scaleY | **1.1 s** | hover-cushion breathe |
| Cushion glow | `cushionGlow` opacity | **1.1 s** | under-hull lift visual |
| Spray particles | `sprayL` translate(−70px, +18px) | **0.75–1.05 s** | debris trails LEFT |
| Wake streaks | `wakeLeft` translateX −180px | **1.4 s** | water trail LEFT |

Propeller transform-origin is anchored inside the thruster group (`translate(-118, 12)` housing + `#propeller` hub).

---

## 3. Narwhal relative motion vs vehicle (≥2 required; 6 present)

| Part | Element | Keyframes | Period | Notes |
|------|---------|-----------|--------|-------|
| Torso bob | `#narwhal-body` | `narwhalBob` | **1.9 s** | ≠ hull 2.4 s → non-locked |
| Hull bob/pitch | `#craft` | `hullBob` | **2.4 s** | vehicle-local baseline |
| Near pectoral | `#flipper-near` | `flipperR` | **1.35 s** + 0.25 s delay | phase-offset |
| Far pectoral | `#flipper-far` | `flipperL` | **1.35 s** | different keyframe angles (−28° vs +32°) |
| Tail flukes | `#tail` | `tailSway` | **1.6 s** | lateral rotate ±14° / +12° + translateX |
| Tusk nod | `#tusk` | `tuskNod` | **2.1 s** | subtle ±2–3° |
| Eye blink | `#eye-lid` | `blink` | **4.2 s** | lid scaleY pulse |

Distinct periods (0.55 / 1.1 / 1.35 / 1.6 / 1.9 / 2.1 / 2.4 / 4.2 s) prevent “whole-body stamp” lockstep.

---

## 4. Parallax / depth layers (far → near)

| ID | Content | Scroll keyframes | Period | Travel |
|----|---------|------------------|--------|--------|
| `#layer-stars` | star field + twinkle | JS pointer parallax (CSS static) | — | slowest |
| `#layer-aurora` | 3 aurora ribbons | `auroraDrift` / `auroraGlow` | 18–24 s | slow |
| `#layer-far` | icebergs | `scrollFar` | **48 s** | −1200 px |
| `#layer-mid` | mid floes | `scrollMid` | **32 s** | −1600 px |
| `#layer-water` | sea + sparks | `scrollWater` | **14 s** | −800 px |
| `#layer-near` | near floes | `scrollNear` | **20 s** | −2200 px |
| `#layer-mist` | foreground mist | `scrollMist` | **10 s** | −2600 px (fastest) |
| `#hero` | craft + narwhal | CSS bob + JS mouse follow | — | hero plane |

JS `requestAnimationFrame` loop smooth-follows the pointer and sets CSS `translate` on each background layer (composites with the CSS `transform` scroll animation) plus a compensating `translate` attribute on `#hero`. Respects `prefers-reduced-motion`.

---

## 5. External dependencies

- No `http(s)://` resource loads (PowerShell regex count = **0** on raw file).
- No `@import`, no `<link rel=stylesheet>`, no external `<script src>`.
- Inline SVG is HTML5 (no `xmlns` attribute needed inside HTML documents).
- Browser `performance.getEntriesByType('resource')` returned **`[]`** (Playwright, file:// load) — zero network requests.
- Fonts: system stack only (`Segoe UI` / `PingFang SC` / `Noto Sans SC` / `system-ui`).
- All gradients/filters defined in inline `<defs>`.

---

## 6. Automated self-check hook

`window.__NARWHAL_DEBUG__` (end of `art.html`) exposes:

```
version, layers(), hasSvg, hasCraft, hasPropeller, hasTail, hasFlippers,
reduceMotion, getComputedAnimations(id)
```

Browser console:
```js
__NARWHAL_DEBUG__.layers()
// expect: stars, aurora, far, mid, water, near, mist
__NARWHAL_DEBUG__.getComputedAnimations('tail')
// expect animationName contains tailSway
```

---

## 7. Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation: none !important; }
}
```
JS also skips rAF loop / boost / click nudge when `reduce` is true.

---

## 8. Aesthetic intent (non-laziness)

- Deep Arctic twilight gradient sky (not white).
- Multi-stop gradients: hull, skin, belly, tusk, glass, skirt, aurora.
- Soft glow filters (`softGlow`, `mistBlur`), cabin light, beacon, headlamp cone.
- Character details: captain’s cap, pink pilot scarf, yoke, speckled skin, spiral tusk ridges, blowhole mist.
- HUD chrome: title + route badge + hint text (Chinese).

See `response.md` for acceptance checklist evidence and UNVERIFIED visual items.
