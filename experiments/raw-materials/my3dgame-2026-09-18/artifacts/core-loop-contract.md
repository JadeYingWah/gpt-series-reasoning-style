# Core Loop Contract

`Player does [steer + fire / dash] to achieve [clear waves / survive] while [incoming asteroids] creates risk; success gives [score + next wave], failure causes [shield 0 → fast retry].`

| Clause | Proof in code |
|--------|----------------|
| verb → input | `InputController.readMovement` + fire/dash intents → `Player` / `Game` |
| objective visible | HUD：波次、分数、护盾；场上陨石与弹道 |
| pressure in first minute | 第 1 波即有持续刷怪，约 10–20s 出现密集区 |
| reward changes state | 分数累加、波次推进、击破粒子与音效 |
| failure teaches | 护盾扣减 + 受击闪白/震屏，归零进 gameover |
| restart fast | Enter / R / 点击「重新出击」立即 `resetRun()` |
