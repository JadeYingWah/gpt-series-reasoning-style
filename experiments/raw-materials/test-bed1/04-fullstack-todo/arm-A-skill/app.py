# -*- coding: utf-8 -*-
"""待办应用后端：Flask JSON API + 页面路由。

数据保存在进程内存中，重启后清空（演示用途，见 README）。
"""
import os
import threading

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

_todos = []          # [{"id": int, "title": str}]
_next_id = 1         # 自增主键
_lock = threading.Lock()


@app.route("/")
def index():
    """前端页面。"""
    return render_template("index.html")


@app.get("/api/todos")
def list_todos():
    """获取全部待办。"""
    with _lock:
        return jsonify({"todos": list(_todos)})


@app.post("/api/todos")
def add_todo():
    """添加待办，请求体 {"title": "..."}；空/纯空白标题返回 400。"""
    global _next_id
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"error": "title 不能为空"}), 400
    with _lock:
        todo = {"id": _next_id, "title": title}
        _next_id += 1
        _todos.append(todo)
    return jsonify(todo), 201


@app.delete("/api/todos/<int:todo_id>")
def delete_todo(todo_id):
    """删除指定待办；不存在返回 404。"""
    with _lock:
        for i, todo in enumerate(_todos):
            if todo["id"] == todo_id:
                _todos.pop(i)
                return jsonify({"deleted": todo_id})
    return jsonify({"error": "todo 不存在"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
