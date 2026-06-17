from flask import Flask, jsonify, request

app = Flask(__name__)

_NOTES = {}
_SEQ = {"n": 0}


@app.get("/notes")
def list_notes():
    return jsonify(list(_NOTES.values()))


@app.post("/notes")
def create_note():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    _SEQ["n"] += 1
    nid = str(_SEQ["n"])
    _NOTES[nid] = {"id": nid, "title": title, "content": content}
    return jsonify(_NOTES[nid]), 201


@app.delete("/notes/<note_id>")
def delete_note(note_id):
    if note_id not in _NOTES:
        return jsonify(error="not found"), 404
    _NOTES.pop(note_id, None)
    return jsonify(ok=True)
