# response · WG010-pomodoro-lite（A-skill）

交付：`pomodoro.html`（单文件）+ 本文件。附带 `verify-core.js` 为逻辑核对脚本（非 UI 交付物）。

## 已核对项（有证据）

| 验收项 | 结果 | 证据 |
|--------|------|------|
| 文件存在 | ✓ | `pomodoro.html` 已写入本目录 |
| 开始/暂停/重置逻辑自洽 | ✓ | Node 抽取 `PomodoroCore` 后 43/43 通过（见 `verify-core.js`） |
| 时长配置 1–60 正整数 | ✓ | `parseMinutes`：1/25/60/`"10"` 接受；0/61/2.5/-1/`"abc"`/空/null 拒绝 |
| 倒计时与到时 | ✓ | 假时钟：30s 暂停 remaining=30；恢复后 t 到 0 时 `onDone` 恰好 1 次，remaining=0，再次 start 返回 false |
| 重置 | ✓ | done 后 reset 回到 full 60s，非 running |
| 到时状态可见 | ✓ | 源码含文案「时间到」，`onDone` 写入 `#status` class `done` |
| 无外链/CDN | ✓ | 源码无 `http(s)://`、无 cdn/googleapis/unpkg/jsdelivr/cdnjs/google fonts |
| 可配置 UI | ✓ | `#minutes` `min="1" max="60" step="1"`，非法输入回滚并提示 |
| 提示音 | ✓（实现） | Web Audio API 880Hz sine，0.7s 衰减；无 AudioContext 时静默失败不阻断状态 |

### Node 核对命令

```bash
node verify-core.js
# 期望：PASS 43 FAIL 0
```

### 设计说明（A-skill）

按 frontend-design 做了刻意选择：暖纸色桌面仪表风格（非默认近黑+霓虹），番茄红环形进度为签名元素，数字用等宽 tabular-nums。交互按钮 ≥44px，含 `:focus-visible`，动画有 `prefers-reduced-motion` 分支。无 CDN/框架。

## 浏览器交互 UNVERIFIED

以下依赖真实浏览器/DOM/用户手势，**本环境未做实机点验**，请自行打开 `pomodoro.html` 验证：

1. **打开页面** → 显示 `25:00`，状态「就绪」，环满。
2. **点「开始」** → 数字递减，环顺时针缩短，状态「进行中」，按钮变「暂停」，时长输入禁用。
3. **点「暂停」** → 数字停住，状态「已暂停」，按钮回「开始」，时长可再改。
4. **再点「开始」** → 从暂停处继续。
5. **点「重置」** → 回到当前配置时长满值，状态「就绪」，按钮「开始」且可点。
6. **改时长** → 输入 `1` 点「应用」→ 显示 `01:00`；输入 `0`/`61`/`abc` → 提示「请输入 1–60 的正整数」且不破坏当前计时。
7. **到时**（可先把时长设为 1 分钟，或改源码临时缩短）→ 显示 `00:00`，状态「**时间到」**，开始按钮禁用；应听到短 beep（若浏览器策略拦截自动音频，属预期，状态文案仍会出现）。
8. **窄屏** → 约 375px 宽无横向滚动。

## 验收清单

- [x] 文件存在
- [x] 开始/暂停/重置逻辑自洽
- [x] 时长配置生效
- [x] 到时状态可见
- [x] 无外链
- [x] response 有证据或 UNVERIFIED
