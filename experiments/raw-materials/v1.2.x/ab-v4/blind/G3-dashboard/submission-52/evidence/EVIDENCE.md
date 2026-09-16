# A2 证据报告（轻量配置·精简版）

任务：G3 静态数据看板 · skill 快照 gpt-series-reasoning-style v1.2.1 · 轻量（验证聚焦版）

## 交付物
- `../index.html`：单文件看板。12 个月销售数据内联（SALES 数组，万元）；3 指标卡（总额/月均值/峰值月）；内联 SVG 趋势图（折线+面积+数据点标签，Y 轴自动 nice 刻度）；筛选控件（全年/四季度，按钮组）。无外部依赖、无 CDN，双击可开。

## 验证（可复现命令）
1. **数据独立复算**：`python evidence/verify_data.py`
   - 从 index.html 正则提取 SALES（不手抄），独立计算各范围 total/avg/peak，输出 JSON 预期值。结果：all=2036/169.7/12月(268)；q1=366/122.0/3月(142)；q2=466/155.3/6月(173)；q3=501/167.0/9月(187)；q4=703/234.3/12月(268)。
2. **初始渲染**：`"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --dump-dom file:///<实验根目录>/ab-v4/G3-dashboard/A2/index.html > evidence/dom-initial.html`
   - 指标卡初始值 2,036 万 / 169.7 万 / 12月，与复算一致；SVG 已生成。
3. **CDP 真实交互**：`node evidence/cdp_verify.js`（Chrome headless + WebSocket，结果见 `evidence/cdp_result.json`）
   - 5 个筛选状态 × 逐项比对：3 指标卡文本、peakHint、active 按钮及背景色 getComputedStyle=rgb(37,99,235)、SVG 图表数值/月份序列、Y 轴首刻度 0 —— 全部与 Python 预期一致，`pass: true`。
   - 错误三通道采集：页面 onerror/unhandledrejection、console.error 事件、Runtime.exceptionThrown —— 均 0 条。
   - 截图 `screenshot-all.png`、`screenshot-q1.png` 已人工目验（active 高亮、卡片/图表切换、无文字遮挡）。
4. **第 1 轮审查**（含验证）：功能正确性/数据一致性（数据、图表标签、指标卡同源）/边界（无并列峰值；n=1 有保护不触发；按钮键盘可达；viewBox 响应式；≤640px 单列）/UX（hover+active 反馈、标签防遮挡 yMax≥max）/目标一致性 —— 无新问题。

## 声明对照
- 轻量配置跳过模块：任务参照系→一句话目标声明；完整资源盘点→摘要（无适用已装 skill）；循环审查 2轮→1轮；宿主对齐跳过。实际执行与声明一致。
- 简化项清单：无（任务书要求项全部实现）。
- 类型判断：混合类（代码+数据），数据类核心验证（独立复算）已执行；未做网络搜索（任务规格完整指定，轻量精简）。

## 边界与残留
- 写入仅限 <实验根目录>\ab-v4\G3-dashboard\A2\；Chrome 临时 profile（evidence/.chrome-tmp）已清理；无全局进程操作。
- UNVERIFIED 项：无。验证均在真实 Chrome headless 环境实操（非纯静态断言）；真实人工目视仅覆盖 2 张截图，其余 3 个季度状态以 DOM/样式断言为证。
