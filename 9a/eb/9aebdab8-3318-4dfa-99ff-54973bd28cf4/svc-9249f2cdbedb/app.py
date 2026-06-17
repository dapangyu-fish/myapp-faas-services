from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

_BOOKMARKS = {}
_SEQ = {"n": 0}

CATEGORIES = ["工作", "学习", "生活", "工具", "娱乐"]


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M")


def _bookmark_dict(bm):
    return {
        "id": bm["id"],
        "title": bm["title"],
        "url": bm["url"],
        "category": bm["category"],
        "notes": bm.get("notes", ""),
        "created_at": bm["created_at"],
        "updated_at": bm["updated_at"],
    }


@app.get("/bookmarks")
def list_bookmarks():
    category_filter = request.args.get("category")
    search = request.args.get("search", "").strip()
    bookmarks = list(_BOOKMARKS.values())
    if category_filter and category_filter in CATEGORIES:
        bookmarks = [b for b in bookmarks if b["category"] == category_filter]
    if search:
        q = search.lower()
        bookmarks = [
            b for b in bookmarks
            if q in b["title"].lower() or q in b["url"].lower() or q in b.get("notes", "").lower()
        ]
    bookmarks.sort(key=lambda b: b["created_at"], reverse=True)
    return jsonify([_bookmark_dict(b) for b in bookmarks])


@app.post("/bookmarks")
def create_bookmark():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(error="title is required"), 400
    url = (body.get("url") or "").strip()
    category = body.get("category", "工作")
    if category not in CATEGORIES:
        category = "工作"
    _SEQ["n"] += 1
    bid = str(_SEQ["n"])
    now = _now()
    _BOOKMARKS[bid] = {
        "id": bid,
        "title": title,
        "url": url,
        "category": category,
        "notes": body.get("notes", ""),
        "created_at": now,
        "updated_at": now,
    }
    return jsonify(_bookmark_dict(_BOOKMARKS[bid])), 201


@app.get("/bookmarks/<bookmark_id>")
def get_bookmark(bookmark_id):
    bm = _BOOKMARKS.get(bookmark_id)
    return (jsonify(_bookmark_dict(bm)), 200) if bm else (jsonify(error="not found"), 404)


@app.put("/bookmarks/<bookmark_id>")
def update_bookmark(bookmark_id):
    if bookmark_id not in _BOOKMARKS:
        return jsonify(error="not found"), 404
    body = request.get_json(silent=True) or {}
    bm = _BOOKMARKS[bookmark_id]
    if "title" in body:
        title = (body["title"] or "").strip()
        if not title:
            return jsonify(error="title is required"), 400
        bm["title"] = title
    if "url" in body:
        bm["url"] = (body["url"] or "").strip()
    if "category" in body:
        cat = body["category"]
        if cat in CATEGORIES:
            bm["category"] = cat
    if "notes" in body:
        bm["notes"] = body["notes"]
    bm["updated_at"] = _now()
    return jsonify(_bookmark_dict(bm))


@app.delete("/bookmarks/<bookmark_id>")
def delete_bookmark(bookmark_id):
    _BOOKMARKS.pop(bookmark_id, None)
    return jsonify(ok=True)
