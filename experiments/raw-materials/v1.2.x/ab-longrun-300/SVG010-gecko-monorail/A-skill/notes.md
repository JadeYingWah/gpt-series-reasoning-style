# Notes — SVG010-gecko-monorail · Neon Dusk Line

## Subject

A vivid green gecko conductor pilots a single-rail monorail through a neon dusk
cityscape. Advance axis is **+X (frame right)**. The world scrolls **−X** under
the train so the train reads as pushing forward to the right.

## Design direction (frontend-design pass 1)

| Token | Value | Role |
|-------|-------|------|
| night | `#07141f` | deepest sky / vignette |
| deep | `#0d2436` | mid sky / far skyline |
| dusk | `#1a3d55` | upper atmosphere |
| ember | `#c45a28` | sunset band at horizon |
| lime | `#7cb518` | gecko primary |
| lime-deep | `#4f8a0e` | gecko outlines / limbs |
| belly | `#f0d060` | ventral / toe pads / eyes |
| neon | `#3de7e7` | monorail glow, rail ticks, yoke |
| pink | `#ff4f9a` | racing stripe, tongue, thruster rim |
| body-shell | `#e8eef2` → `#8fa3b0` | carriage shell gradient |

- **Mode**: expressive creative scene (not a UI surface).
- **Signature**: glowing open-cockpit gecko against the monorail nose, tail
  swaying on a period different from the train bob.
- **Risk taken**: saturated tropical night-neon palette — deliberately rejects
  “white background + flat gray icon” lazy default.
- **Type**: Georgia italic for route caption only; scene itself is pure SVG.

## Geometry & motion self-consistency

### 1. Forward direction vs cyclic animations

| Element | Animation | Direction logic |
|---------|-----------|-----------------|
| Magnetic wheels (×4) | CSS `spin-cw` 360° / 0.55s | Clockwise on a rail whose contact point is below → rolls toward +X (right). Matches train advance. |
| Thruster streams | `thrust-stream` translateX 0 → −24px, loop 0.35s | Streaks flow toward −X (left of bogie). Action-reaction: exhaust left ⇒ thrust right. |
| Thruster core | opacity pulse 0.45s | Brightens at exhaust nozzle (rear, left side of bogie). |
| Rail ticks (`p-rail`) | translateX 0 → −800px / 6s | Fixed marks slide left ⇒ vehicle moves right. |
| Headlight cone | static ellipse at nose (right) | Points along +X. |

### 2. Gecko appendages with relative motion (not locked to vehicle)

Vehicle root `.train-root` only bobs `translateY` 0↔4px over **2.4s**.
Gecko limbs each have their **own** transform + period:

| Appendage | Class | Motion | Period | Independent of bob? |
|-----------|-------|--------|--------|---------------------|
| Tail | `.gecko-tail` | rotate −7°↔9° + slight skewX | 1.7s | yes (different period & axis) |
| Left arm (throttle) | `.gecko-arm-l` | rotate −6°↔12° | 1.15s | yes |
| Right arm (wave) | `.gecko-arm-r` | rotate 4°→−28°→18° | 2.1s | yes |
| Head | `.gecko-head` | rotate 4°↔−5° + translateY | 3.3s | yes |
| Hind leg | `.gecko-leg-back` | rotate 0↔−8° tap | 0.95s | yes |
| Eyelids | JS `.blink` | scaleY 0→1→0 | random 2.2–6.0s | yes |
| Tongue | JS `.flick` | scaleX 0→1→0 | random 5–14s | yes |

≥2 required; delivered **7** distinct relative channels.

### 3. Background parallax layers (≥2 required; delivered 4)

All use the same seamless dual-strip technique: content is drawn twice across
`0–1600` and animated `translateX 0 → −800px` so the wrap is invisible.

| Layer | Class | Duration | Relative speed | Content |
|-------|-------|----------|----------------|---------|
| L0 sky | static | — | 0 | gradient, stars |
| L1 far | `.p-far` | 48s | 1.0× | moon glow, far skyline silhouette |
| L2 mid | `.p-mid` | 22s | ~2.2× | lit towers, palm silhouettes |
| L3 near | `.p-near` | 11s | ~4.4× | utility poles, cyan speed streaks |
| L4 rail | `.p-rail` | 6s | 8× | rail tick marks |

Faster layers are nearer → classic depth cue.

### 4. Reduced motion

`@media (prefers-reduced-motion: reduce)` disables all CSS loops; JS skips
scheduling blink/tongue when that media query matches.

## Accessibility

- SVG has `role="img"` and a descriptive `aria-label`.
- Caption is decorative (`pointer-events: none`, `user-select: none`).
- No keyboard traps; page is a non-interactive scene.

## Self-consistency anchors in `art.html`

| Concern | Where to look |
|---------|----------------|
| Advance axis declaration | comment at train group (~L505): `ADVANCE AXIS: +X` |
| Wheel roll direction | `.wheel-spin` + `@keyframes spin-cw` (~L171–178, wheels ~L602–639) |
| Thruster action-reaction | `.thrust-stream` left of bogie (~L584–596); exhaust −X ⇒ thrust +X |
| Parallax speed ladder | `.p-far/.p-mid/.p-near/.p-rail` durations 48/22/11/6s (~L72–75) |
| Appendage independence | separate groups `.gecko-tail/.gecko-arm-l/.gecko-arm-r/.gecko-head/.gecko-leg-back` |
| Reduced motion | CSS `@media (prefers-reduced-motion: reduce)` (~L240) + JS guard (~L802) |

## Files

| File | Role |
|------|------|
| `art.html` | single-file deliverable (CSS/JS/SVG inline), 36155 bytes |
| `notes.md` | this document (geometry / motion / design tokens) |
| `response.md` | verification evidence & UNVERIFIED items |
| `load-proof.md` | skill load proof (phase 1) |
| `task.md` | local acceptance brief |
| `verify-shot.png` | headless Chrome still (post-cockpit fix) |
| `verify-shot-t2.png` | second Chrome still (repeat capture) |
| `verify-pw-t0.png` | Playwright t≈0.3s |
| `verify-pw-t1.png` | Playwright t≈2.8s (wheel phase + parallax delta) |

## Stage-2 closeout note

`art.html` was **not** rewritten in closeout: structural checks + screenshot
review found no hard defect. Remaining aesthetic nits are logged in
`response.md` (UNVERIFIED / known-minor), not patched here.
