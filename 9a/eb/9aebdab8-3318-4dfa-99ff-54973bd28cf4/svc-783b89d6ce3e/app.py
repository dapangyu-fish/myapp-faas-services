from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

_NOTES = {}
_SEQ = {"n": 0}


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _note_dict(note):
    return {
        "id": note["id"],
        "title": note["title"],
        "content": note["content"],
        "created_at": note["created_at"],
    }


@app.get("/notes")
def list_notes():
    notes = list(_NOTES.values())
    notes.sort(key=lambda n: n["created_at"], reverse=True)
    return jsonify([_note_dict(n) for n in notes])


@app.post("/notes")
def create_note():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    content = (body.get("content") or "").strip()
    _SEQ["n"] += 1
    nid = str(_SEQ["n"])
    now = _now()
    _NOTES[nid] = {
        "id": nid,
        "title": title,
        "content": content,
        "created_at": now,
    }
    return jsonify(_note_dict(_NOTES[nid])), 201


@app.delete("/notes/<note_id>")
def delete_note(note_id):
    _NOTES.pop(note_id, None)
    return jsonify(ok=True)
