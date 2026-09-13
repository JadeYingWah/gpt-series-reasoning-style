# Notes · SVG007-heron-zeppelin · A-skill

## Deliverable

- `art.html` — single-file HTML/SVG. CSS + comments inline. No CDN, no framework, no network requests.

## Scene

- **Subject**: a grey heron pilot standing in an open cockpit of a rigid-body zeppelin (envelope + struts + gondola + tail fins + nose propeller).
- **Heading**: +X (screen right). Nose cone, beak, propeller, thrust streaks, and rudder bar all point right.
- **Time of place**: dusk / early night sky, warm cabin lights, cool sky gradient.

## Motion self-consistency

### 1. Propeller / thrust (must agree with travel direction)

- Propeller is a 2-blade disc at the nose (`#propeller`), spinning about a vertical hub via `transform-origin` on the hub.
- Spin is clockwise from the pilot's view → blade disc drags air aft → thrust streaks (`x1=438 → x2=470+`) paint wake **to the right**, matching the craft's heading.
- Companion `#prop-wash` dashed ring flickers in phase with the blade cycle (0.28s), selling rotational blur.

### 2. Parallax / depth (≥ 2 background layers)

Three independent scroll groups, all moving **left** (opposite of rightward flight), with different periods so nearer layers pass faster:

| Layer | Group           | Contents                         | Cycle |
|-------|-----------------|----------------------------------|-------|
| Far   | `#layer-far`    | stars, moon, constellation lines | 80s   |
| Mid   | `#layer-mid`    | soft cloud banks (blurred)       | 36s   |
| Near  | `#layer-near`   | hill silhouettes + low clouds    | 18s   |

Wrap tiles extend beyond x=1200 so the slide reads continuous at the viewBox edge.

### 3. Heron limbs vs vehicle (must NOT be lockstep)

Vehicle body `#zeppelin-rig` bobs on a **3.2s** ease-in-out cycle (translateY + slight pitch). Every articulated heron part uses a **different** period and/or phase:

| Part                 | Selector              | Period | Relative motion |
|----------------------|-----------------------|--------|-----------------|
| Neck + head          | `#heron-neck-head`    | 2.4s   | rotate about neck base |
| Crest feathers       | `#heron-crest`        | 1.1s   | rotate + skew flutter |
| Near wing            | `#heron-wing`         | 1.6s   | rotate + scaleY flap |
| Far wing             | `#heron-wing-far`     | 1.6s, delay −0.35s | phase-offset rotate |
| Trailing leg         | `#heron-leg-trail`    | 3.7s   | rotate about hip |
| Rudder foot          | `#heron-foot-rudder`  | 4.5s   | translateX press on bar |

Because no limb shares the vehicle's 3.2s period, the heron cannot be read as a rigid sprite glued to the gondola.

## Style

- Not white-background / not default flat icon. Uses radial moon glow, linear sky/envelope gradients, soft blur filters, rib/seam geometry on the envelope, and caption typography.
- Registration mark `HZ-07` on the hull for craft identity.

## Constraints honored

- Only files written inside `A-skill/`.
- Single file, fully offline.
