# DESIGN.md — 弗糯糯炒饭

## 1. Objective

玩家打开游戏后 3 秒内感到「这是给弗洛洛粉丝做的手绘节奏小品」：二次元写实手绘质感、指挥家×炒饭的反差萌、一局 60 秒内打完的爽快节奏。品质条：可完整游玩一局、判定清晰、角色立绘点题、视觉不落入通用 AI 模板。

## 2. Product Context

- **What the product does:** 单页 HTML 节奏烹饪游戏——按键跟拍把「弗糯糯炒饭」从生米炒到出锅。
- **Who it's for:** 《鸣潮》弗洛洛爱好者、喜欢轻量节奏游戏/同人小品的玩家。
- **Adjacent brands (feel like these):** 《Project Sekai》的谱面 HUD 气质；《料理妈妈》的做菜反馈；同人 zine 手绘封面的纸感。
- **Distant brand (do not feel like this):** 赛博霓虹电竞风——全屏渐变紫青 + 未来 HUD，与「手绘、炒饭、指挥家」三件套冲突。
- **Cultural register:** playful（反差萌）+ 一点舞台剧的仪式感（她是指挥家）。

## 3. Visual Foundations

### 3a. Color

- **Neutral scale:** `--n-900: #1A1218`（舞台幕布深底）、`--n-800: #2A1F2E`、`--n-600: #5C4A55`、`--n-300: #C4B5A8`、`--n-100: #F3E6D4`（奶油纸面）
- **Accent:** `--accent: #C43B4A`（彼岸花红 / 弗洛洛瞳色系）；次强调 `--hair: #6F9B5A`（发色绿）、`--gold: #E8C547`（Perfect 判定）
- **Semantic:** `--perfect: #E8C547`、`--great: #6F9B5A`、`--miss: #5C4A55`
- **Usage rules:** 深底铺满全屏；奶油纸面只用于面板/卡片；红只出现在标题点睛、判定条、角色配饰；绿只绑定角色与 Great；金只绑定 Perfect。禁止把 accent 铺成大面积背景渐变。

### 3b. Typography

- **Display face:** `"STKaiti", "KaiTi", "Noto Serif SC", "Songti SC", serif`——手写感标题，tracking 略松。
- **Body face:** `"PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif`。
- **Fallback stack:** 上列顺序即回退；布局不依赖 web font。
- **Type scale:** 12 / 14 / 16 / 20 / 28 / 40 / 64。
- **Weight discipline:** 标题 700；HUD 数字 700 tabular；正文 400；判定词 700。禁止三级以上字重混用。

### 3c. Spacing & rhythm

- **Base unit:** 8px。
- **Spacing scale:** 8, 16, 24, 32, 48, 64。
- **What "generous" means:** 舞台区四周 ≥ 48px 安全边；谱面与 HUD 间距 ≥ 24px。

### 3d. Component seeds

- **Button:** 2 个变体——主按钮（奶油底 + 深墨字 + 细描边，手绘圆角 12px）、幽灵按钮（透明底 + 描边）。一屏最多一个实心主按钮。
- **Card / container:** 用「纸片」隐喻：`--n-100` 底、2px 深墨描边、轻微旋转 ±1°，不用默认 shadow-sm 网格。
- **Iconography:** 食材与判定用小 SVG/字符，不用 emoji 装饰标题。
- **Note chip:** 谱面音符=食材圆片（米白/蛋黄/葱绿/酱红四色描边）。

## 4. Accessibility

- **Text contrast:** 正文对底 ≥ 4.5:1；大标题 ≥ 3:1。
- **Motion:** 尊重 `prefers-reduced-motion`；打击特效可降级为闪色。
- **Focus indicators:** 2px 金色描边 + 2px offset。
- **Alt text:** 角色立绘 alt=「弗糯糯 Q 版指挥家」；纯装饰纹理 aria-hidden。

## 5. Voice & Tone

- **Register:** playful，带一点指挥家台词腔。
- **Sentence rhythm:** 短句为主（HUD/判定 1–4 字；引导句 ≤ 12 字）。
- **Words this brand uses:** 起锅、跟拍、Perfect、开演、出锅。
- **Words this brand refuses:** 无缝、赋能、极致体验、沉浸式生态。
- **Address:** 「你」——「按 D 键下米」。

## 6. Implementation Practices

- **Token format:** CSS variables 在 `:root`。
- **Component library convention:** 无框架，vanilla HTML/CSS/JS。
- **Image treatment rules:** 手绘插画作背景/角色；谱面与 HUD 纯 CSS/SVG；图片全部本地 `assets/`，禁止运行时外链。
- **Grid system:** 游戏主区居中单列（max-width ~960px 舞台）；谱面 4 轨等分。
- **Motion rules:** ease-out 120–260ms；打击反馈用 scale+opacity；无无意义循环动画（除待机呼吸）。

## 7. Anti-Patterns

- **No purple-cyan gradient hero.** 舞台深色是单色幕布，不是霓虹渐变。
- **No rounded-16 shadow card grid.** 面板是歪一点的纸片，不是 shadcn 默认卡。
- **No emoji on headers.** 标题用字与描边装饰。
- **No "seamlessly" copy.** 文案必须指具体操作（「按 F 打蛋」）。
- **No dual y-axis / KPI row.** HUD 只要分数、连击、进度三个数。

## 8. Decision-Making

1. **节奏判定清晰 > 装饰华丽。** 冲突时先保轨道对比度与判定窗可读。
2. **角色辨识度 > 写实比例。** 弗糯糯是 Q 版，保留绿发/异色瞳/彼岸花/指挥棒，比例可夸张。
3. **单屏完成一局 > 多菜单系统。** 不做设置页/多歌曲选单。
4. **本地素材可用 > 远程高清。** 加载失败的图必须有 CSS 底色回退。

## 9. Workflow

1. 写定本 DESIGN.md。
2. 生成/落地本地素材到 `assets/`。
3. 竖切：标题 → 一局谱面 → 结算，先通。
4. 手感打磨：判定窗、连击、打击音（WebAudio 合成）。
5. 视觉对齐 token 与反 slop 自检。
6. 浏览器真开验证后再交。

---

## 结构（本作）

| # | 类型 | 一句话 |
|---|------|--------|
| 1 | cover/title | 「弗糯糯炒饭」开演：标题 + Q 版指挥家 + 开始 |
| 2 | how-to | 三行操作说明：D/F/J/K 对应四轨食材 |
| 3 | gameplay | 4 轨下落谱面 + 底部炒锅进度 + 分数/连击 HUD |
| 4 | results | 评级（S/A/B/C）+ 成品炒饭插画 + 再来一局 |

**玩法规格（竖切即完整）：**
- 4 轨：D 米饭 / F 蛋液 / J 葱花 / K 酱油
- BPM≈120，单曲约 45–60s，手工谱面一张
- 判定：Perfect ±80ms / Great ±140ms / Miss >140ms 或漏键
- 连击、分数、锅中「完成度」进度条；结束进结算
- 音效：WebAudio 合成鼓点+判定音，不依赖外部音频文件

**Image manifest：**

| 用途 | 来源 | 主题 | 朝向 | 路径 |
|------|------|------|------|------|
| 标题/主视觉 Q 版角色 | image_gen | 弗糯糯：绿发异色瞳 Q 版指挥家，拿指挥棒兼锅铲 | 竖/方 | `assets/furuan.png` |
| 舞台厨房背景 | image_gen | 深色幕布+暖光灶台，手绘 | 横 | `assets/stage-bg.png` |
| 成品炒饭 | image_gen | 一碗金黄炒饭，手绘 | 方 | `assets/dish.png` |

## Decision Trace（摘录）

1. **深色舞台而非奶油满屏** — 指挥家开演隐喻 + 谱面需要高对比；备选奶油全屏（更 zine 但谱面弱）；代价：暖度靠纸片面板补。
2. **4 轨食材键而非环形轨道** — 上手成本最低；备选环形/太鼓；代价： less 独特，靠食材色与锅进度找记忆点。
3. **WebAudio 合成曲** — 零外部依赖可离线；备选生成 mp3；代价：旋律简单。
4. **Q 版保留异色瞳与彼岸花** — 粉丝辨识关键；备选简化成通用 chibi；代价：立绘生成难度略高。
