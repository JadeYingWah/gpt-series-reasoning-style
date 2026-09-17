# 任务包：dashboard + report

## 背景
个人财务月度套件（2025）。指挥官已定稿唯一数据源 `js/data.js` 与入口 `index.html`、共享样式 `css/style.css`。你需要基于同一份数据完成两个内容页。

## 已定决策
- 工作目录：`C:\Users\<username>\Desktop\MyProject`
- 数据：浏览器加载 `js/data.js` 后使用 `window.FinanceData`（含 `months` / `summary` / `incomeCategories` / `expenseCategories` / `formatMoney`）
- 图表：仅用原生 Canvas 手绘，禁止外部图表库 / CDN / 网络字体
- 样式：优先复用 `css/style.css` 中的 class（`.page` `.panel` `.card` `.data` `.legend` 等），可在自己的 JS 旁补少量页面级样式（可写在 HTML 的 `<style>` 或新建 `css/dashboard.css` / `css/report.css`，但不得改 `js/data.js` 与 `css/style.css` 的已有语义）
- 导航：页头与 index 一致（首页 / 仪表盘 / 月度报告）

## 未定缺口
无。数据与入口已锁。

## 完成标准
1. `dashboard.html` + `js/dashboard.js` 可双击离线打开，无控制台报错。
2. `report.html` + `js/report.js` 可双击离线打开，无控制台报错。
3. 仪表盘至少包含：
   - 月度收入/支出对比柱状图（Canvas）
   - 月度净结余折线或面积图（Canvas）
   - 全年支出构成（分类占比条/环，Canvas）
   - 顶部 KPI：年收入、年支出、净结余、储蓄率（均来自 FinanceData）
4. 报告页至少包含：
   - 12 个月汇总表（月份 / 收入 / 支出 / 结余），合计行正确
   - 支出分类合计表或列表
   - 由数据推导的文字分析（至少 3 段：整体财务状况、异常或高峰月、主要开支观察）
5. 页面上的每一个数字都能与 `js/data.js` 对上（禁止手写死数字作为汇总结论；图表坐标可四舍五入展示但底层数来自数据）。
6. 不引入任何外部资源。

## 允许范围
- 新建/修改：`dashboard.html`、`report.html`、`js/dashboard.js`、`js/report.js`、可选 `css/dashboard.css`、`css/report.css`
- 可读：`js/data.js`、`index.html`、`css/style.css`

## 禁止范围
- 禁止修改 `js/data.js`
- 禁止修改 `index.html`、`css/style.css`、`docs/**`
- 禁止安装依赖、起本地服务、访问网络

## 唯一 DRI
执行者 frontend

## 交回给谁
指挥官（本会话主 Agent）验收。交回时说明：做了什么 / 怎么自验的 / 哪些没验。
