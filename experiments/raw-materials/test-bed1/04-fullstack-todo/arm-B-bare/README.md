# 待办应用（Flask + 原生 HTML/JS）

一个极简的全栈待办（Todo）应用：Flask 提供 REST API，前端单页通过 `fetch` 与后端交互，支持添加、展示、勾选完成、删除待办。

## 目录结构

```
arm-B-bare/
├── app.py              # Flask 后端（页面路由 + REST API）
├── requirements.txt    # Python 依赖
├── templates/
│   └── index.html      # 前端页面（原生 HTML/CSS/JS）
└── README.md
```

## 环境要求

- Python 3.8+
- pip

## 运行步骤

```bash
# 1. 进入本目录
cd arm-B-bare

# 2. （可选）创建并激活虚拟环境
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python app.py
```

启动后在浏览器打开：**http://127.0.0.1:5000**

## API 说明

| 方法 | 路径 | 说明 | 请求体 | 成功响应 |
|------|------|------|--------|----------|
| GET | `/api/todos` | 获取全部待办 | — | `{"todos": [{"id":1,"title":"...","done":false}]}` |
| POST | `/api/todos` | 添加待办 | `{"title": "买牛奶"}` | `201` + 新建的待办对象 |
| PUT | `/api/todos/<id>` | 切换完成/未完成 | — | 更新后的待办对象 |
| DELETE | `/api/todos/<id>` | 删除待办 | — | `{"deleted": <id>}` |

## 前后端交互方式

- 页面由 Flask 渲染（`GET /` 返回 `templates/index.html`）。
- 前端 JavaScript 通过 `fetch` 调用 `/api/todos` 系列接口：
  - 页面加载时 `GET /api/todos` 拉取列表并渲染；
  - 点击「添加」或回车 → `POST /api/todos` 提交 JSON → 重新拉取列表；
  - 勾选复选框 → `PUT /api/todos/<id>` 切换完成状态；
  - 点击「删除」→ `DELETE /api/todos/<id>`。

## 已知限制

- 数据存储在内存中，服务重启后待办清空（演示用途）。
- 调试模式开启（`debug=True`），仅限本地开发使用。
