# Final Evidence — Neon Void (My3DGame)

## Build
- `npm run build` → tsc + vite OK (pass-4 revision)
- Bundle: ~619 kB JS (gzip ~160 kB), CSS ~5.5 kB

## Local run
- Dev: `npm run dev` → http://127.0.0.1:5188
- Controls: WASD/摇杆移动 · 鼠标左键/J/FIRE 射击 · Space/DASH 冲刺（无敌帧）· Enter/R 重开

## Design artifacts
- [design-brief.md](design-brief.md)
- [core-loop-contract.md](core-loop-contract.md)
- [level-plan.md](level-plan.md)

## Tests
- `npx playwright test` → **6 passed** (desktop + mobile layouts)
  - visual: nonblank canvas + W-move input
  - gameplay: start → move → fire → victory hook → restart; idle → game over → restart

## Canvas inspector (runId pass-4)
- Desktop active-play: nonblank, colorEntropyBits=2.45, budget OK (calls 46 / tri 5822)
- Mobile active-play: nonblank, colorEntropyBits=3.03, budget OK (calls 34 / tri 3374)
- Desktop complete: nonblank, victory state, score 1200 hook
- Console/page errors: none

## Evidence check
- `check_evidence.py . --manifest artifacts/evidence.json` → pass (see final run)

## Known limitations
- Not AAA premium scorecard pass (scope: 扎实完成 + 霓虹科幻)
- Mobile Playwright project uses Chromium emulation (WebKit binary absent)
- Audio pitch uses Math.random (non-gameplay); VFX/gameplay use seeded RNG
