# response · SVG010-gecko-monorail（B 臂）

## 实际核对项

| 验收项 | 结果 | 证据 |
|--------|------|------|
| `art.html` 存在且 ≥8KB | ✅ | 文件长度 32142 字节（node 校验） |
| 含 SVG 或 canvas 主体 | ✅ | 根节点 `<svg id="stage" viewBox="0 0 1280 720">`，完整 gecko + monorail + 城市 |
| 有动画（CSS 或 JS） | ✅ | `<script>` 内 `requestAnimationFrame(loop)` 驱动轮转、视差、附肢 |
| 两层以上背景/视差 | ✅ | L0/L1/L2/L4 + 轨枕，速度 0 / 18 / 42 / 160 / 280 px/s |
| 附肢与载具非完全同步 | ✅ | 见 `notes.md` §2：head/arm/tail/leg/blink 独立相位 |
| 无外部资源依赖 | ✅ | 无 `http(s)://` 引用、无 CDN、无 `fetch`/`@import`/外链字体（可用 grep 复核） |
| 自洽说明存在 | ✅ | `notes.md` + `art.html` 顶部 HTML 注释 |
| response 有证据或 UNVERIFIED | ✅ | 本表 |

## 自动化无法覆盖 / 标 UNVERIFIED 的视觉项

以下需用户在浏览器中肉眼确认（本环境无图形渲染截图回读）：

1. **UNVERIFIED — gecko 可辨认度**
   - 用户自验：用浏览器打开 `art.html`，应能一眼看出驾驶舱内是蜥蜴（大眼、绿皮、吸盘趾、长尾），而非色块。
2. **UNVERIFIED — monorail 可辨认度**
   - 用户自验：应能看出是高架单轨列车（长车身、流线头、轨上磁垫、受电弓），朝画面右侧行驶。
3. **UNVERIFIED — 轮/轨循环与前进方向一致**
   - 用户自验：观察磁垫滚轮辐条是否**顺时针**转；轨枕与近景柱是否**向左**掠过。
4. **UNVERIFIED — 视差景深感**
   - 用户自验：远楼慢、中楼中速、近柱快，三层速度应肉眼可分。
5. **UNVERIFIED — 附肢相对运动明显**
   - 用户自验：盯住车头 3 秒，尾巴摆动、前肢推杆、后脚点地、偶发眨眼应与车体小幅颠簸不同步。
6. **UNVERIFIED — 无控制台错误**
   - 用户自验：F12 → Console，应无红字。

## 文件清单（本目录）

- `task.md`（任务书，未改）
- `art.html`（交付主体）
- `notes.md`（几何/运动自洽）
- `response.md`（本文件）

## 禁止项遵守

- 未读取 `<skill安装目录>
- 未修改本目录以外文件。
