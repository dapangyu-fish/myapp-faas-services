from __future__ import annotations
from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


def _row_to_dict(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "url": row["url"],
        "tag": row["tag"],
        "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
    }


@app.get("/bookmarks")
def list_bookmarks():
    rows = myapp_db.query(
        "SELECT id, title, url, tag, created_at FROM bookmarks ORDER BY id DESC"
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


@app.delete("/bookmarks/<int:bookmark_id>")
def delete_bookmark(bookmark_id):
    n = myapp_db.execute("DELETE FROM bookmarks WHERE id = %s", [bookmark_id])
    if n == 0:
        return jsonify(error="not found"), 404
    return jsonify(ok=True, id=bookmark_id)
