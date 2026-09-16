"""待办应用 - Flask 后端 API"""
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# 内存存储：服务重启后数据清空（演示用途，足够覆盖添加/展示/删除/勾选）
todos = []
_next_id = 1


def _next():
    global _next_id
    tid = _next_id
    _next_id += 1
    return tid


# ---------- 页面路由 ----------
@app.route("/")
def index():
    return render_template("index.html")


# ---------- REST API ----------
@app.route("/api/todos", methods=["GET"])
def list_todos():
    return jsonify({"todos": todos})


@app.route("/api/todos", methods=["POST"])
def add_todo():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    todo = {"id": _next(), "title": title, "done": False}
    todos.append(todo)
    return jsonify(todo), 201


@app.route("/api/todos/<int:todo_id>", methods=["PUT"])
def toggle_todo(todo_id):
    for todo in todos:
        if todo["id"] == todo_id:
            todo["done"] = not todo["done"]
            return jsonify(todo)
    return jsonify({"error": "待办不存在"}), 404


@app.route("/api/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    for i, todo in enumerate(todos):
        if todo["id"] == todo_id:
            todos.pop(i)
            return jsonify({"deleted": todo_id})
    return jsonify({"error": "待办不存在"}), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
