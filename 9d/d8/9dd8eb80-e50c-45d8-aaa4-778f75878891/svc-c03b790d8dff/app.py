from flask import Flask, jsonify, request

app = Flask(__name__)

_NOTES = {}
_SEQ = {"n": 0}


def _serialize(note_id, payload):
    return {
        "id": note_id,
        "title": payload.get("title", ""),
        "content": payload.get("content", ""),
        "seq": payload.get("seq", 0),
    }


@app.get("/notes")
def list_notes():
    items = [_serialize(nid, data) for nid, data in _NOTES.items()]
    items.sort(key=lambda x: x.get("seq") or 0, reverse=True)
    return jsonify({"notes": items}), 200


@app.post("/notes")
def create_note():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    content = (body.get("content") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    _SEQ["n"] += 1
    nid = str(_SEQ["n"])
    _NOTES[nid] = {
        "title": title,
        "content": content,
        "seq": _SEQ["n"],
    }
    payload = _serialize(nid, _NOTES[nid])
    return jsonify(payload), 201


@app.delete("/notes/<note_id>")
def delete_note(note_id):
    existed = note_id in _NOTES
    _NOTES.pop(note_id, None)
    return jsonify({"ok": True, "existed": existed}), 200
