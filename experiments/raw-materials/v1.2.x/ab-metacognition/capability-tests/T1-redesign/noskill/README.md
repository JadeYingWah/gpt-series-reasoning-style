# 待办 Web 应用

一个功能完整的待办事项管理 Web 应用，支持添加、查看、完成、删除待办，数据持久化存储。

## 功能特性

- ✅ 添加待办事项（标题、描述、优先级、截止日期）
- ✅ 查看所有待办列表
- ✅ 标记完成 / 取消完成
- ✅ 编辑待办内容
- ✅ 删除待办事项
- ✅ 按状态筛选（全部 / 未完成 / 已完成）
- ✅ 多种排序方式（创建时间、截止日期、优先级）
- ✅ 优先级颜色标识（高/中/低）
- ✅ 截止日期逾期提醒
- ✅ 数据持久化（SQLite，重启不丢失）
- ✅ 响应式 Web 界面

## 技术栈

- **后端**: Node.js + Express
- **数据库**: SQLite（better-sqlite3，文件型，无需额外安装数据库服务）
- **前端**: 原生 HTML / CSS / JavaScript（无构建步骤）

## 项目结构

```
noskill/
├── package.json      # 项目依赖配置
├── server.js         # Express 服务器 + REST API
├── db.js             # SQLite 数据库模块
├── public/
│   ├── index.html    # 前端页面
│   ├── style.css     # 样式
│   └── app.js        # 前端逻辑
├── data/             # 运行时自动创建，存放 SQLite 数据库文件
└── README.md
```

## 运行说明

### 环境要求

- Node.js >= 18（已在 v22 验证）

### 启动步骤

```bash
# 1. 进入项目目录
cd noskill

# 2. 安装依赖
npm install

# 3. 启动服务
npm start
```

启动后终端会显示：

```
Todo app running at http://localhost:3000
```

### 访问

在浏览器中打开 **http://localhost:3000**

### 自定义端口

默认端口为 3000，可通过环境变量修改：

```bash
# Windows (PowerShell)
$env:PORT=8080; npm start

# Linux / macOS
PORT=8080 npm start
```

## API 接口

| 方法   | 路径                  | 说明           |
|--------|-----------------------|----------------|
| GET    | `/api/todos`          | 获取所有待办   |
| GET    | `/api/todos/:id`      | 获取单个待办   |
| POST   | `/api/todos`          | 创建待办       |
| PUT    | `/api/todos/:id`      | 更新待办       |
| PATCH  | `/api/todos/:id/toggle` | 切换完成状态 |
| DELETE | `/api/todos/:id`      | 删除待办       |

### 请求体示例（创建/更新）

```json
{
  "title": "完成项目报告",
  "description": "包含Q3数据分析和下季度计划",
  "priority": "high",
  "due_date": "2026-09-30"
}
```

- `title` (必填): 待办标题
- `description` (可选): 待办描述
- `priority` (可选): `low` / `medium` / `high`，默认 `medium`
- `due_date` (可选): 格式 `YYYY-MM-DD`

## 验证说明

### 1. 服务启动验证

运行 `npm start` 后，终端输出 `Todo app running at http://localhost:3000`，无报错。

### 2. 页面访问验证

浏览器打开 http://localhost:3000，应看到待办应用界面，包含：
- 顶部标题"待办事项"
- 添加表单（标题、描述、优先级、截止日期、添加按钮）
- 筛选栏（全部/未完成/已完成）和排序下拉
- 空状态提示"暂无待办事项"

### 3. 功能验证流程

1. **添加**: 在标题输入"测试任务"，选择优先级"高"，设置截止日期，点击"添加" → 列表出现新条目
2. **查看**: 列表显示标题、描述、优先级标签、截止日期
3. **完成**: 点击条目左侧复选框 → 条目变灰、标题加删除线，计数更新
4. **编辑**: 点击 ✏️ 按钮 → 弹出编辑弹窗，修改后保存 → 列表更新
5. **删除**: 点击 🗑️ 按钮 → 确认后条目消失
6. **筛选**: 点击"未完成"/"已完成"按钮 → 列表按状态过滤
7. **排序**: 切换排序下拉 → 列表顺序变化

### 4. 持久化验证

1. 添加几条待办事项
2. 在终端按 `Ctrl+C` 停止服务
3. 重新运行 `npm start`
4. 刷新浏览器 → 之前添加的待办仍然存在

### 5. API 快速验证（可选）

```bash
# 创建待办
curl -X POST http://localhost:3000/api/todos \
  -H "Content-Type: application/json" \
  -d '{"title":"API测试","priority":"medium"}'

# 查看所有
curl http://localhost:3000/api/todos

# 标记完成
curl -X PATCH http://localhost:3000/api/todos/1/toggle \
  -H "Content-Type: application/json" \
  -d '{"completed":true}'

# 删除
curl -X DELETE http://localhost:3000/api/todos/1
```

## 数据存储

数据库文件位于 `data/todos.db`，删除该文件即可清空所有数据并重置应用。
