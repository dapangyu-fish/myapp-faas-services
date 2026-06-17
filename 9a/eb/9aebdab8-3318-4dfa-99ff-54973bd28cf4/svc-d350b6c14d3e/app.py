from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

_TASKS = {}
_SEQ = {"n": 0}

STATUS_OPTIONS = ["pending", "in_progress", "done"]
STATUS_LABELS = {"pending": "\u5f85\u5904\u7406", "in_progress": "\u8fdb\u884c\u4e2d", "done": "\u5df2\u5b8c\u6210"}


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _task_dict(task):
    return {
        "id": task["id"],
        "title": task["title"],
        "description": task.get("description", ""),
        "status": task["status"],
        "status_label": STATUS_LABELS.get(task["status"], task["status"]),
        "created_at": task["created_at"],
        "updated_at": task["updated_at"],
    }


@app.get("/tasks")
def list_tasks():
    status_filter = request.args.get("status")
    tasks = list(_TASKS.values())
    if status_filter and status_filter in STATUS_OPTIONS:
        tasks = [t for t in tasks if t["status"] == status_filter]
    tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return jsonify([_task_dict(t) for t in tasks])


@app.post("/tasks")
def create_task():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    _SEQ["n"] += 1
    tid = str(_SEQ["n"])
    now = _now()
    status = body.get("status", "pending")
    if status not in STATUS_OPTIONS:
        status = "pending"
    _TASKS[tid] = {
        "id": tid,
        "title": title,
        "description": body.get("description", ""),
        "status": status,
        "created_at": now,
        "updated_at": now,
    }
    return jsonify(_task_dict(_TASKS[tid])), 201


@app.get("/tasks/<task_id>")
def get_task(task_id):
    task = _TASKS.get(task_id)
    return (jsonify(_task_dict(task)), 200) if task else (jsonify(error="not found"), 404)


@app.put("/tasks/<task_id>")
def update_task(task_id):
    if task_id not in _TASKS:
        return jsonify(error="not found"), 404
    body = request.get_json(silent=True) or {}
    task = _TASKS[task_id]
    if "title" in body:
        title = (body["title"] or "").strip()
        if not title:
            return jsonify(error="title is required"), 400
        task["title"] = title
    if "description" in body:
        task["description"] = body["description"]
    if "status" in body:
        new_status = body["status"]
        if new_status in STATUS_OPTIONS:
            task["status"] = new_status
    task["updated_at"] = _now()
    return jsonify(_task_dict(task))


@app.delete("/tasks/<task_id>")
def delete_task(task_id):
    _TASKS.pop(task_id, None)
    return jsonify(ok=True)
