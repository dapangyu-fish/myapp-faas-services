from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


def _tododict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return {"id": row.get("id"), "title": row.get("title"), "done": row.get("done")}
    return {"id": row[0], "title": row[1], "done": row[2]}


@app.get("/todos")
def list_todos():
    rows = myapp_db.query("SELECT id, title, done FROM todos ORDER BY id DESC")
    todos = [_tododict(r) for r in rows]
    return jsonify(todos)


@app.post("/todos")
def create_todo():
    body = request.get_json(silent=True) or {}
    title = body.get("title", "").strip()
    if not title:
        return jsonify(error="title required"), 400
    row = myapp_db.queryone(
        "INSERT INTO todos(title) VALUES (%s) RETURNING id, title, done",
        [title],
    )
    return jsonify(_tododict(row)), 201


@app.put("/todos/<todo_id>")
def toggle_todo(todo_id):
    row = myapp_db.queryone(
        "SELECT id, title, done FROM todos WHERE id=%s", [todo_id]
    )
    if not row:
        return jsonify(error="not found"), 404
    todo = _tododict(row)
    new_done = not todo["done"]
    myapp_db.execute("UPDATE todos SET done=%s WHERE id=%s", [new_done, todo_id])
    todo["done"] = new_done
    return jsonify(todo)


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id):
    n = myapp_db.execute("DELETE FROM todos WHERE id=%s", [todo_id])
    if n == 0:
        return jsonify(error="not found"), 404
    return jsonify(ok=True)
