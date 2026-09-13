# SVG014 · Pangolin × Streetcar — Geometry & Motion Notes

## World model

Camera is fixed. The streetcar + pangolin group sits in a vehicle reference frame
near screen center-right. The world scrolls leftward to imply **rightward** travel.

Normalized ground speed `S = 1.0`.

## Parallax / depth (3+ layers)

| Layer | Content | Speed multiplier | Implementation |
|-------|---------|------------------|----------------|
| Sky   | Gradient + stars + sun/moon | 0 (static) | CSS/SVG |
| FAR   | City skyline silhouettes, sparse lit windows | **0.18** | `#layerFar` JS translate |
| MID   | Shopfronts, trees, poles, street lamps | **0.45** | `#layerMid` JS translate |
| NEAR  | Road curb, lane dashes, rail ties/tracks | **1.00** | `#layerNear` JS translate |
| Dust  | Floating motes | 0.70 | `#layerDust` JS translate |
| Speed lines | Whoosh accents behind car | CSS-only | `@keyframes whoosh` |

Tile wrap width = 1620 px; each layer group is cloned once so the wrap is seamless.
`requestAnimationFrame` advances offsets by `PX_PER_SEC_NEAR * multiplier * dt`.

## Vehicle kinematics

- Streetcar advances **right** (headlamp cone faces right, destination board faces side/front-right).
- **Wheel rotation is CLOCKWISE** for rightward travel (top of wheel goes forward, bottom rolls against rail).
  Spokes + yellow tread notch on `#wheelRim` make rotation direction visually explicit.
- Angular period: front/rear primary wheels 0.55 s / rev; secondary smaller wheels 0.72 s / rev
  (slightly different radii ⇒ slightly different periods, mechanical feel).
- Suspension: body group `.car-bob` — 1.82 s period, 1.2 px vertical amplitude.
- Pantograph: contact shoe on overhead wire; spark flickers independently at 0.18 s steps
  (electrical, not kinematic — intentional non-sync).
- Headlamp glow pulses on a 2.1 s cycle (lighting, not motion lock).

## Pangolin relative motion (NOT locked to vehicle translation)

| Part | Motion | Period | Origin |
|------|--------|--------|--------|
| Head | nod + micro-yaw + micro-lift | **2.35 s** | neck base |
| Near arm | elbow flex, forearm steer ±8–10° | **1.45 s** | shoulder |
| Far arm | counter-phase steer | 1.45 s (delayed/counter) | shoulder |
| Claw tips | lagged micro-drag on wheel rim | 1.45 s with 0 / −0.08 / −0.16 s delays | fingertips |
| Tail base | sway | **2.72 s** | tail root |
| Tail mid | delayed sway | 2.72 s (−0.28 s lag) | mid joint |
| Tail tip | independent curl | **1.91 s** | tip joint |
| Chest | breath scale | **3.1 s** | torso center |
| Eye | blink | 5.7 s | eye center |

Wheel spin is 0.55 s; body bob is 1.82 s; head is 2.35 s; tail is 2.72 s.
These periods are deliberately non-harmonic so the animation never re-syncs
into a single locked loop. **≥2 independent limb motions relative to the car
are present (head, both arms, tail, claws, breath).**

## Direction consistency checklist

- [x] Wheels rotate clockwise (rightward travel).
- [x] World scrolls left (`translate` negative X).
- [x] Headlamp cone and nose point right.
- [x] Pangolin faces right (snout on right of head group).
- [x] Speed lines travel leftward (CSS whoosh).

## Style notes

- Night/dusk city: deep violet sky → warm sunset band. No pure-white background.
- Streetcar: classic crimson body, brass/gold roof and trim, cream destination board
  reading `PANGOLIN · 14`, pantograph, side windows, door, rivets.
- Pangolin: overlapping keratin scale tiles via SVG `<symbol>`, long snout, dark eye,
  clawed hands on the steering wheel, long scaly tail trailing rearward with curl.

## External resources

None. All CSS and JS are inline. No CDN, fonts, images, or network requests.
SVG gradients, filters, and symbols are local `<defs>`.
