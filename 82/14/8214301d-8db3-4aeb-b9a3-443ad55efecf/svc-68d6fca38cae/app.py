from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


@app.get("/todos")
def list_todos():
    rows = myapp_db.query(
        "SELECT id, title, done FROM todos ORDER BY id ASC"
    )
    return jsonify([{"id": r[0], "title": r[1], "done": r[2]} for r in rows])


@app.post("/todos")
def create_todo():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    row = myapp_db.queryone(
        "INSERT INTO todos(title, done) VALUES (%s, %s) RETURNING id, title, done",
        [title, False]
    )
    return jsonify({"id": row[0], "title": row[1], "done": row[2]}), 201


@app.put("/todos/<todo_id>")
def toggle_todo(todo_id):
    existing = myapp_db.queryone(
        "SELECT id, title, done FROM todos WHERE id = %s", [todo_id]
    )
    if not existing:
        return jsonify(error="not found"), 404
    new_done = not existing[2]
    row = myapp_db.queryone(
        "UPDATE todos SET done = %s WHERE id = %s RETURNING id, title, done",
        [new_done, todo_id]
    )
    return jsonify({"id": row[0], "title": row[1], "done": row[2]})


@app.delete("/todos/<todo_id>")
def delete_todo(todo_id):
    existing = myapp_db.queryone(
        "SELECT id FROM todos WHERE id = %s", [todo_id]
    )
    if not existing:
        return jsonify(error="not found"), 404
    myapp_db.execute("DELETE FROM todos WHERE id = %s", [todo_id])
    return jsonify(ok=True)
