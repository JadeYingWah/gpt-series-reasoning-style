# 待办应用（Flask + HTML 前后端交互）

一个最小可用的待办（Todo）应用：Flask 提供 JSON API 并托管前端页面，前端用原生 JS 通过 `fetch` 与后端交互，支持**添加、显示、删除**待办。

## 目录结构

```
arm-A-skill/
├── app.py              # Flask 后端（API + 页面路由）
├── requirements.txt    # Python 依赖
├── README.md
└── templates/
    └── index.html      # 前端页面（原生 JS，fetch 调用 API）
```

## 运行步骤

前提：已安装 Python 3.10+。

1. 进入本项目目录（即本 README 所在目录）。

2. （可选）创建并激活虚拟环境：

   ```bash
   python -m venv .venv
   # Windows (cmd/PowerShell)
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

4. 启动服务：

   ```bash
   python app.py
   ```

   默认监听 `http://127.0.0.1:5000`；如 5000 被占用，可换端口：

   ```bash
   # Windows (PowerShell)
   $env:PORT = "5057"; python app.py
   # macOS / Linux
   PORT=5057 python app.py
   ```

5. 打开浏览器访问 `http://127.0.0.1:5000`（换了端口则用对应端口），在输入框输入内容点「添加」，即可看到列表实时更新。

## API 说明

| 方法   | 路径                 | 说明         | 请求体 / 返回                                  |
| ------ | -------------------- | ------------ | ---------------------------------------------- |
| GET    | `/api/todos`         | 获取全部待办 | 返回 `{"todos": [{"id": 1, "title": "..."}]}`  |
| POST   | `/api/todos`         | 添加待办     | 请求体 `{"title": "事项"}`，成功返回 201       |
| DELETE | `/api/todos/<id>`    | 删除指定待办 | 成功返回 `{"deleted": id}`；id 不存在返回 404  |
| GET    | `/`                  | 前端页面     | HTML                                           |

接口示例：

```bash
curl http://127.0.0.1:5000/api/todos
curl -X POST http://127.0.0.1:5000/api/todos -H "Content-Type: application/json" -d "{\"title\": \"buy milk\"}"
curl -X DELETE http://127.0.0.1:5000/api/todos/1
```

## 说明与限制

- 数据保存在**进程内存**中，重启服务后清空（演示用途，未做持久化）。
- 服务默认只监听本机 `127.0.0.1`，局域网其他设备不可访问。
- 空标题 / 纯空白标题会被拒绝：前端直接提示，后端返回 400（双保险）。
- 前端渲染待办标题使用 `textContent`，输入 HTML/脚本内容不会被注入执行。
