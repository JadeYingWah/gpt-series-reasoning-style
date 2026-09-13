# 个人作品集网站

一个符合 2026 年前端最佳实践的响应式个人作品集网站。

## 功能特性

- 🏠 **首页**：个人介绍、6项技能展示、3个精选项目
- 💼 **项目展示**：6个项目、4类筛选（全部/Web/移动端/设计）
- 👤 **关于页**：个人简介、工作经历时间线、教育背景、认证荣誉
- 📧 **联系页**：完整表单验证、3种联系方式
- 📱 **响应式设计**：Mobile-first，375px/768px/1024px 三断点
- ♿ **无障碍**：skip-link、ARIA 标签、键盘导航、减少动效偏好
- ⚡ **性能优化**：无外部依赖、CSS 变量系统、Intersection Observer 懒动画
- 🎨 **现代化视觉**：深色主题、渐变、微动效、毛玻璃导航

## 技术栈

- HTML5（语义化标签）
- CSS3（CSS 变量、Flexbox、Grid、Mobile-first）
- 原生 JavaScript（IIFE、无框架依赖）

## 项目结构

```
portfolio/
├── index.html          # 首页
├── projects.html       # 项目展示页
├── about.html          # 关于页
├── contact.html        # 联系页
├── css/
│   └── style.css       # 主样式表（含响应式/无障碍/打印样式）
├── js/
│   └── main.js         # 主脚本（导航/验证/筛选/动画）
├── assets/             # 静态资源目录
└── README.md           # 说明文档
```

## 使用方法

直接在浏览器中打开 `index.html` 即可。

## 浏览器兼容性

- Chrome 90+ / Edge 90+
- Firefox 88+
- Safari 14+

## 无障碍特性

- 跳过导航链接（skip-link）
- 所有交互元素有 ARIA 标签
- 表单有错误提示和 aria-describedby
- 支持 `prefers-reduced-motion`
- 焦点可见样式
- 语义化 HTML 结构

## 已知限制

- 表单提交为前端模拟，未连接后端服务
- 项目详情链接为占位符
- 图片为 CSS 渐变占位，未使用真实图片
- 无 404 页面（静态站点，需服务器配置）

## 许可证

MIT License
