from __future__ import annotations
import myapp_db
from flask import Flask, jsonify, request

app = Flask(__name__)


def _row_to_dict(row):
    return {
        "id": row.get("id"),
        "title": row.get("title") or "",
        "url": row.get("url") or "",
        "tag": row.get("tag") or "",
        "created_at": row.get("created_at").isoformat() if row.get("created_at") else None,
    }


@app.get("/bookmarks")
def list_bookmarks():
    rows = myapp_db.query(
        "SELECT id, title, url, tag, created_at FROM bookmarks ORDER BY id DESC LIMIT 200"
    )
    return jsonify([_row_to_dict(r) for r in rows])


@app.post("/bookmarks")
def create_bookmark():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    url = (body.get("url") or "").strip()
    tag = (body.get("tag") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    if not url:
        return jsonify(error="url is required"), 400
    row = myapp_db.queryone(
        "INSERT INTO bookmarks(title, url, tag) VALUES (%s, %s, %s) "
        "RETURNING id, title, url, tag, created_at",
        [title, url, tag],
    )
    return jsonify(_row_to_dict(row)), 201


@app.delete("/bookmarks/<bookmark_id>")
def delete_bookmark(bookmark_id):
    try:
        bid = int(bookmark_id)
    except (TypeError, ValueError):
        return jsonify(error="invalid id"), 400
    n = myapp_db.execute("DELETE FROM bookmarks WHERE id = %s", [bid])
    if not n:
        return jsonify(error="not found"), 404
    return jsonify(ok=True, id=bid)
