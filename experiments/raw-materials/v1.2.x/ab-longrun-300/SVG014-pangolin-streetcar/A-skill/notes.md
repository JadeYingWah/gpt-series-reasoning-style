# notes.md — SVG014 motion self-consistency

Authoritative geometry/motion notes for `art.html`. HTML comments mirror this; this file is the full write-up.

## Scene contract

| Item | Value |
|------|--------|
| Forward axis | **+X (screen right)** |
| Subject | pangolin in cab of vintage streetcar |
| Subject screen x | roughly 640–990 of viewBox `0 0 1200 640` (stable) |
| World motion | layers translate **negative X** (leftward scroll) |
| Visual pitch | twilight / wet night city, route 7 eastbound |

The streetcar **holds a stable x**; the world slides left. That is the standard "camera tracking" setup for rightward travel.

---

## 1. Propulsion & world scroll (direction self-consistent)

### Wheels

- IDs: rear wheel group origin `(700,430)`, front wheel group origin `(880,430)`, r=28.
- Animation: `@keyframes spin-wheel` → `rotate(0deg)` → `rotate(360deg)`, duration **0.55s**, linear infinite.
- CSS/SVG positive rotation is **clockwise** when viewed from the default side.
- Clockwise + rail contact = **rightward** vehicle travel.
- Each wheel has a red **timing mark** at local top `(cy-26)` so rotation direction is readable in motion, not just a blur.

### Street / rail feedback

- `#street` group: `translateX(0 → -720px)` over **6s** linear infinite.
- Contains dual rails, rail ties every 60px, curb stones — all scroll left, matching implied rightward car speed.
- Tie spacing (60px) × 40 repeats covers 2400px, so one loop period covers >2× viewport width (1200), avoiding a visible hard cut.

### Parallax speed ladder (faster = nearer)

| Layer | id | ΔX / period | Relative speed |
|-------|-----|-------------|----------------|
| Stars | `#stars` | -120px / 28s | slowest (far) |
| Far skyline | `#far-city` | -280px / 18s | slow |
| Mid city (trees, shops, lamps) | `#mid-city` | -520px / 10s | medium |
| Street surface | `#street` | -720px / 6s | fastest (near) |

Four scrolling layers; task requires ≥2. Relative order is monotonic (faster when nearer), so depth reads correctly.

### Overhead wire / pantograph

- Catenary paths at y≈190–208 (world-fixed y, not scrolled with street).
- Pantograph tip circle sits at y≈195 on the upper wire.
- `#panto` sways ±1.2° independently (1.1s) against car body bob (0.72s) — spring/pantograph lag.

### Headlight

- Housing at **x≈958** (front of car), beam path extends to **x=1100** (rightward).
- Confirms facing direction = forward = +X.

---

## 2. Pangolin relative motion (≥2 independent, actually 5)

Car body `#car-body` bobs on `car-bob` **0.72s**. All pangolin sub-parts use **different periods** and **different transform-origins**, so none is a rigid child of the bob:

| Part | id | Animation | Period | Why not locked |
|------|-----|-----------|--------|----------------|
| Head / snout | `#pango-head` | `head-look` rotate+Y | **2.6s** | 3.6× car period; neck joint origin |
| Front arm + claw | `#pango-arm-front` | `arm-pump` rotate | **1.35s** | shoulder origin; pumps lever |
| Controller lever | `#controller-lever` | `lever-shift` rotate | **1.35s** | same phase family as arm (causal link), not car-bob |
| Tail | `#pango-tail` | `tail-sway` rotate | **1.9s** | hip/counterbalance origin |
| Rear claw | `#pango-arm-rear` | `rear-claw` Y+rotate | **2.1s** | footplate plant/shift |
| Torso breathe | `#pango-torso` | `pango-body-breathe` Y+scaleY | **1.05s** | scales catch light under cab lamp |

Five independent pangolin motions vs car bob; arm↔lever is a deliberate coupled pair (driver action), not a lock-to-vehicle bug.

### Pangolin ID cues (static geometry)

- Long tapered snout path past the eye.
- Overlapping kite-shaped scale paths (`url(#pangoScaleGrad)`) on torso, head, tail.
- Stout ellipsoid torso + lighter belly.
- Long digging claws on front and rear limbs.
- Thick scaled tail with tapering scale rows.

---

## 3. Secondary motion / atmosphere

- `#spark`: travels right→left along wire (relative wind), 1.8s.
- `#wet-sheen`: opacity shimmer 3.2s under car (wet asphalt).
- `#rain`: slanted fall (-18px X, +760px Y) 1.15s — matches relative wind from motion.
- Lamp glows: 2.4s with staggered delays so street lamps don't pulse in unison.
- Pointer nudge (JS): small additive `translate` on `#far-city` / `#mid-city` only; disabled under `prefers-reduced-motion`.

---

## 4. Accessibility / constraints

- Single file; CSS + one optional IIFE script; **no CDN, no fetch, no external URLs**.
- `prefers-reduced-motion: reduce` freezes all listed loops (parallax, bob, pangolin parts, spark, rain, wheels).
- SVG has `title` / `desc` for screen readers.
- `preserveAspectRatio="xMidYMid slice"` fills stage without letterboxing the car.

## 5. Known residual risks (honest)

- Wheel spin period (0.55s) is artistic; not calibrated to a real km/h vs street-tie scroll rate. Visually coherent; physical ground-speed match is approximate.
- `translate` CSS property for pointer parallax requires a modern Chromium; older Safari may ignore the nudge (scene still works via CSS animations).
- Nested `<style>` inside SVG for wheels is intentional (self-contained wheel keyframes); valid in HTML5 inline SVG.
