# A/B 技术方案提案（AB-PROPOSAL）

> 项目：T1 待办 Web 应用重设计（skill 条件组）
> 生成时间：2026-09-13
> 状态：🔴 等待用户确认

---

## 方案 A：Node.js + Express + SQLite + 原生多文件前端

### 架构概览

```
浏览器 (原生 HTML/CSS/JS)
    │  fetch / REST JSON
    ▼
Express 服务器 (:3000)
    │  better-sqlite3 (同步 API, 预编译语句)
    ▼
SQLite 文件 (data/todos.db, WAL 模式)
```

### 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 运行时 | Node.js | v22（本机已验证） |
| 后端框架 | Express | ^4.19 |
| 数据库驱动 | better-sqlite3 | ^11.3（原生模块，预编译） |
| 前端 | 原生 HTML + CSS + Vanilla JS | 无构建步骤 |
| 包管理 | npm | 10.9（本机已验证） |

### 项目结构

```
skill/
├── package.json
├── server.js          # Express 服务器 + 路由
├── db.js              # SQLite 数据层（建表、预编译语句、CRUD）
├── public/
│   ├── index.html     # 页面结构
│   ├── style.css      # 样式
│   └── app.js         # 前端逻辑
├── data/              # 运行时生成 todos.db
└── README.md
```

### API 设计（6 端点）

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | /api/todos | 列表 |
| GET | /api/todos/:id | 详情 |
| POST | /api/todos | 创建 |
| PUT | /api/todos/:id | 更新 |
| PATCH | /api/todos/:id/toggle | 切换完成 |
| DELETE | /api/todos/:id | 删除 |

### 优势

1. **实验变量纯净**：与 noskill 对照组完全同技术栈，A/B 实验仅测量流程纪律差异，结果可直接对比
2. **依赖已验证**：Node v22 + npm 在本机已跑通，better-sqlite3 原生模块编译成功
3. **行业最经典组合**：搜索结果中多篇 Todo App 教程采用 Express+SQLite/MonboDB，生态成熟
4. **前后端分离清晰**：public/ 静态托管，API 与静态文件解耦
5. **better-sqlite3 同步 API**：代码简洁，预编译语句防 SQL 注入，性能好

### 劣势

1. **与对照组同栈**：若实验目的是测试"不同技术栈 + 流程纪律"的组合效果，则方案 A 无法提供技术栈多样性
2. **原生模块依赖**：better-sqlite3 需要 native build 工具链，在某些精简环境可能安装失败（本机已验证通过）
3. **前端无组件化**：Vanilla JS 操作 DOM 代码量较大，交互复杂时维护成本上升

### 启动命令

```bash
cd skill
npm install
npm start
# → http://localhost:3000
```

---

## 方案 B：Python + FastAPI + SQLite(stdlib) + 单文件内嵌前端

### 架构概览

```
浏览器 (单 HTML，内联 CSS/JS)
    │  fetch / REST JSON
    ▼
FastAPI 服务器 (:8000)
    │  sqlite3 (Python 标准库, 无第三方 DB 依赖)
    ▼
SQLite 文件 (data/todos.db)
```

### 技术栈

| 层 | 技术 | 版本 |
|---|---|---|
| 运行时 | Python | 3.14（本机已验证） |
| 后端框架 | FastAPI | ^0.115（含 Uvicorn ASGI 服务器） |
| 数据库驱动 | sqlite3 | Python 标准库（零额外依赖） |
| 前端 | 单 HTML 文件内联 CSS+JS | 无构建步骤，无外部静态文件 |
| 包管理 | pip | 随 Python |

### 项目结构

```
skill/
├── requirements.txt   # fastapi, uvicorn
├── main.py            # FastAPI 应用 + 路由 + DB 初始化
├── database.py        # SQLite 数据层（stdlib sqlite3）
├── templates/
│   └── index.html     # 单文件前端（内联 CSS/JS）
├── data/              # 运行时生成 todos.db
└── README.md
```

### API 设计（6 端点，与方案 A 功能对齐）

| 方法 | 路径 | 功能 |
|---|---|---|
| GET | /api/todos | 列表 |
| GET | /api/todos/{id} | 详情 |
| POST | /api/todos | 创建（Pydantic 模型校验） |
| PUT | /api/todos/{id} | 更新 |
| PATCH | /api/todos/{id}/toggle | 切换完成 |
| DELETE | /api/todos/{id} | 删除 |

**额外特性**：FastAPI 自动生成 `/docs`（Swagger UI）和 `/openapi.json`，API 可交互调试。

### 优势

1. **技术栈完全不同**：Python 生态 vs Node 生态，为实验提供技术栈多样性维度
2. **零 DB 第三方依赖**：sqlite3 是 Python 标准库，无需 native build，安装更轻量可靠
3. **自动 API 文档**：FastAPI 基于 Pydantic 类型注解自动生成 Swagger UI，开箱即用
4. **原生异步**：ASGI 架构，天然支持异步，虽本任务不需要但扩展性好
5. **单文件前端**：templates/index.html 内联所有 CSS/JS，静态资源管理更简单
6. **Pydantic 数据校验**：请求体自动校验（类型、必填、枚举），减少手动校验代码

### 劣势

1. **实验变量混入**：与 noskill 对照组技术栈不同，A/B 对比时无法分离"流程纪律效果"和"技术栈效果"
2. **Python 3.14 较新**：部分包可能尚未完全兼容 3.14（FastAPI/uvicorn 通常兼容，但需验证）
3. **单文件前端**：HTML 文件较大，CSS/JS/HTML 混在一起，不如多文件分离清晰
4. **前端无 Node 生态**：无法使用 npm 前端工具链（虽本任务用原生即可）
5. **异步 sqlite3**：stdlib sqlite3 是同步 API，在 async 路由中需用 run_in_executor 或接受阻塞（对 Todo App 量级无影响）

### 启动命令

```bash
cd skill
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# → http://localhost:8000
# API 文档 → http://localhost:8000/docs
```

---

## 两方案实质性差异对比

| 维度 | 方案 A | 方案 B |
|---|---|---|
| 运行时 | Node.js v22 | Python 3.14 |
| 后端框架 | Express (回调式, 同步) | FastAPI (ASGI, 异步, 类型注解) |
| DB 驱动 | better-sqlite3 (第三方 native) | sqlite3 (标准库) |
| 依赖数量 | 2 个直接依赖 (express, better-sqlite3) + native build | 2 个直接依赖 (fastapi, uvicorn), 无 native |
| 前端组织 | 多文件分离 (html/css/js) | 单文件内联 |
| API 文档 | 手写 README | 自动 Swagger UI |
| 请求校验 | 手动 if 检查 | Pydantic 自动校验 |
| 端口 | 3000 | 8000 |
| 与对照组同栈 | ✅ 是 | ❌ 否 |
| 安装可靠性 | 需 native 编译（本机已验证） | 纯 Python，更可靠 |

---

## 推荐

**推荐方案 A**。核心理由：本任务是 A/B 对照实验的 skill 组，实验目的是测量"gpt-series-reasoning-style 流程纪律"对产出质量的增量效果。方案 A 与 noskill 对照组采用完全相同的技术栈，确保唯一变量是流程纪律，实验结果最具说服力。方案 B 虽然在工程上有其优势（自动文档、stdlib DB），但会引入技术栈混淆变量，降低实验内部效度。

**如用户明确希望测试"不同技术栈 + 流程纪律"的组合效果**，则方案 B 是合理选择。

---

## 待确认问题

1. **选择方案 A 还是方案 B？**（推荐 A）
2. **前端是否保持原生无框架？**（两方案均默认原生，如需 Alpine.js/React 请说明）
3. **功能范围是否包含筛选/排序/编辑弹窗/逾期标记？**（推荐包含，与对照组对齐）
4. **确认后是否立即开始实现，无需进一步逐项问答？**
