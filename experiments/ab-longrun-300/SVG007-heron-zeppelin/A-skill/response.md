# Response · SVG007-heron-zeppelin · A-skill

## Acceptance checklist (actually checked)

| Item | Status | Evidence |
|------|--------|----------|
| `art.html` exists and ≥ 8KB | **VERIFIED** | File size 24154 bytes (PowerShell `Length`) |
| Contains SVG (or canvas) main drawing | **VERIFIED** | Root `<svg id="stage" viewBox="0 0 1200 700">` draws envelope, gondola, heron, hills, clouds, stars |
| Has animation (CSS or JS) | **VERIFIED** | Inline `<style>` defines multiple `@keyframes` + `animation:` (prop spin, bob, wing flap, neck sway, three drift layers) |
| ≥ 2 background / parallax layers | **VERIFIED** | `#layer-far` (80s), `#layer-mid` (36s), `#layer-near` (18s) — three layers, distinct periods |
| Limbs not fully sync-locked to vehicle | **VERIFIED** | Vehicle bob = 3.2s; limbs use 1.1 / 1.6 / 2.4 / 3.7 / 4.5s and far-wing phase delay −0.35s (see notes.md table) |
| No external resource dependencies | **VERIFIED** | No `<link>`, no `<script src>`, no `http(s)://` asset loads, no CDN fonts. Grep of file shows only xmlns namespace URI |
| Self-consistency notes exist | **VERIFIED** | HTML comment block at bottom of `art.html` + full `notes.md` |
| response has evidence or UNVERIFIED | **VERIFIED** | This file |

## Direction / geometry self-check (static inspection)

- **Forward = right**: nose cone at +X of envelope; beak tip points right; propeller nacelle on nose; thrust streaks extend to larger X.
- **Propeller axis**: vertical hub, blades elongated in Y so rotation sweeps a disc whose wake is painted aft of the nose (rightward craft motion).
- **Heron identity**: long S-neck, long orange beak, crest plumes, long legs, grey/white body — not a generic blob.
- **Zeppelin identity**: elongated envelope with rib seams, tail fins (V/H), struts to gondola, cabin windows, nose prop.

## Visual / runtime items — UNVERIFIED (need human eye)

These cannot be confirmed by file inspection alone:

1. **Perceived animation quality** — open `art.html` in a browser; confirm propeller looks like spinning blades (not a stuck shape), wing flap reads as lift, and cloud drift is smooth (no harsh jump at wrap).
2. **Parallax readability** — confirm the three layers clearly feel at different depths while the craft stays framed.
3. **Heron readability at a glance** — zoom to ~50% window size; the bird should still read as a heron, not a lump.
4. **Overall composition** — subject not clipped at common viewports (try 1280×800 and 1920×1080); caption not overlapping the craft.

### User self-verify steps

```
1. Double-click A-skill/art.html (or open in Chrome/Firefox/Edge).
2. Watch for 5–10 seconds:
   - propeller disc spinning at nose
   - zeppelin body gently bobbing
   - heron neck swaying and near wing flapping at a different rhythm than the body
   - far stars / mid clouds / near hills sliding left at different speeds
3. Resize window narrower — SVG should letterbox/scale without breaking layout.
4. DevTools → Network: confirm zero external requests (only the local file).
```

## Files written (this directory only)

- `art.html`
- `notes.md`
- `response.md`

## Residual risk

- No automated visual regression / screenshot in this environment; acceptance items above marked UNVERIFIED remain for human glance.
- Propeller is a stylized 2-ellipse disc + dashed wash ring, not a motion-blurred mesh — acceptable for the brief, but lower-fidelity than a shader/canvas blur.
