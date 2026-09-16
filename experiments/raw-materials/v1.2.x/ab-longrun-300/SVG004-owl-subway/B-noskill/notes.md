# SVG004-owl-subway · Geometry & Motion Coherence Notes

Single-file deliverable: `art.html`. No external resources.

## Scene brief

An owl drives a subway train. The train faces **right (+X)** and the whole
scene is composed so rightward travel is unambiguous: nose cone, windshield
rake, headlight beam, bumper, and destination board all aim +X.

## Forward-direction consistency

| Element | How it matches +X travel |
|---|---|
| Train shell | Nose (front cab) is on the right; rear coupler on the left |
| Headlight | Radial beam path extends from lamp toward x=1280 (right) |
| Wheels | CSS `spin-cw` (clockwise). Contact patch at the rail therefore moves backward (−X) relative to the train — the physical requirement for rightward roll |
| Sleepers | CSS scroll translates −80 px over 0.55 s (same period as one wheel revolution), so ground scroll and wheel spin are phase-locked in perceived speed |
| Exhaust puffs | Rise and drift −X (backward), consistent with roof vent on a rightward-moving car |
| Speed streaks | Translate −X in front of the train |
| Drive gear | Counter-clockwise (`spin-ccw`), reads as a meshing gear under the chassis |
| Owl pupils | Offset to the right inside the irises — driver looking ahead |

## Owl relative motion (appendages NOT locked to train translation)

The train body has only a subtle suspension bounce (0.55 s, ±1.5 px).
The owl has **five independent DOFs**:

1. **Head** — rotate + translateY bob, period 1.6 s (`owl-head`)
2. **Left wing** — flap rotate/scale, period 0.7 s (`owl-wing-l`)
3. **Right wing** — flap rotate/scale, period 0.7 s, opposite phase (`owl-wing-r`)
4. **Tail feathers** — twitch rotate, period 1.1 s (`owl-tail`)
5. **Claw on lever** — grip pulse rotate, period 0.9 s (`owl-claw`)

Plus a body micro-bounce at 0.55 s (matches wheel period — reads as
suspension, not a locked translation of the whole owl).

Blink is a separate SMIL animation on the eye circles (period 3.4 s),
independent of every CSS keyframe above.

## Parallax / depth (≥ 2 layers; this scene has 4)

| Layer | `data-depth` | Content |
|---|---|---|
| L0 far | 0.05 | Sky gradient, stars (with SMIL twinkle), moon + glow, distant skyline |
| L1 mid | 0.18 | Mid-rise buildings with lit windows, elevated track pillars + cross-beams |
| L2 near | 0.55 | Track bed, ballast, sleepers (CSS scroll), rails, third rail, signal poles, foreground weeds |
| Streaks | n/a | CSS speed lines in front of the train as an extra depth cue |

A `requestAnimationFrame` loop applies:
- constant world-scroll (−X) scaled by depth
- slow sinusoidal camera sway
- eased mouse parallax (pointer-driven, passive)

Sleepers additionally use pure CSS translation so ground motion works
even if JS is restricted.

## Timing table (periods)

| Animation | Period | Driver |
|---|---|---|
| Wheel spin (CW) | 0.55 s | CSS |
| Drive gear (CCW) | 0.38 s | CSS |
| Sleeper scroll | 0.55 s (80 px) | CSS |
| Train bounce | 0.55 s | CSS |
| Owl head | 1.6 s | CSS |
| Owl wings | 0.7 s | CSS |
| Owl tail | 1.1 s | CSS |
| Owl claw | 0.9 s | CSS |
| Owl body bounce | 0.55 s | CSS |
| Eye blink | 3.4 s | SMIL |
| Star twinkle | 1.9–3.1 s | SMIL |
| Signal pulse | 2.0 s | CSS |
| Window flicker | 3.2 s | CSS |
| Exhaust puffs | 1.8 s (staggered) | CSS |
| Speed streaks | 0.7 s (staggered) | CSS |
| Parallax drift | continuous | JS rAF |

## Style / anti-laziness

- Custom night-city palette; no white background
- Every shape is hand-authored path/rect/ellipse with gradients, strokes, and glows
- No default flat placeholder icons; owl is a multi-part character (ear tufts, facial disc, belly feather marks, independent wings/tail/claws, catchlight eyes)
- Subway is a multi-part vehicle (body, livery band, passenger windows, door, route badge, cab, windshield, headlight + beam, bumper/cowcatcher, bogies, wheels with spokes + direction notch, drive gear, pantograph, coupler, destination board)
