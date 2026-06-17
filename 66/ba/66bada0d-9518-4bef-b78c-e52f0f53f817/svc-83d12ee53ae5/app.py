from flask import Flask, jsonify, request

app = Flask(__name__)

_NOTES = {}
_SEQ = {"n": 0}


def _next_id():
    _SEQ["n"] += 1
    return str(_SEQ["n"])


def _serialize(note_id, payload):
    return {
        "id": note_id,
        "title": payload.get("title", ""),
        "content": payload.get("content", ""),
        "created_at": payload.get("created_at", ""),
    }


@app.get("/notes")
def list_notes():
    items = [_serialize(nid, n) for nid, n in _NOTES.items()]
    # newest first
    items.sort(key=lambda x: x["id"], reverse=True)
    return jsonify(notes=items, count=len(items))


@app.post("/notes")
def create_note():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    nid = _next_id()
    _NOTES[nid] = {
        "title": title,
        "content": content,
        "created_at": "2026-06-17T00:00:00Z",
    }
    return jsonify(note=_serialize(nid, _NOTES[nid])), 201


@app.delete("/notes/<note_id>")
def delete_note(note_id):
    if note_id not in _NOTES:
        return jsonify(error="not found"), 404
    _NOTES.pop(note_id, None)
    return jsonify(ok=True, id=note_id)
