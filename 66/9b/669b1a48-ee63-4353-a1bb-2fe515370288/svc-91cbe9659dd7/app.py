"""二手物品交易后端：商品 CRUD + 列表查询，Postgres 持久化。"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, request

import myapp_db

app = Flask(__name__)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_item(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "price": float(row["price"]) if row["price"] is not None else 0.0,
        "category": row["category"] or "其他",
        "description": row["description"] or "",
        "created_at": row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["created_at"] else None,
    }


@app.get("/items")
def list_items():
    category = (request.args.get("category") or "").strip()
    query = (request.args.get("q") or "").strip()
    sql = "SELECT id, title, price, category, description, created_at FROM items"
    where = []
    params = []
    if category and category != "全部":
        where.append("category = %s")
        params.append(category)
    if query:
        where.append("(title ILIKE %s OR description ILIKE %s)")
        params.append("%" + query + "%")
        params.append("%" + query + "%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT 200"
    rows = myapp_db.query(sql, params)
    items = [_row_to_item(r) for r in rows]
    return jsonify(ok=True, items=items, count=len(items), time=_now_iso())


@app.post("/items")
def create_item():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(ok=False, error="标题不能为空"), 400
    try:
        price = float(body.get("price") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="价格必须是数字"), 400
    if price < 0:
        return jsonify(ok=False, error="价格不能为负"), 400
    category = (body.get("category") or "其他").strip() or "其他"
    description = (body.get("description") or "").strip()
    row = myapp_db.queryone(
        "INSERT INTO items(title, price, category, description) "
        "VALUES (%s, %s, %s, %s) "
        "RETURNING id, title, price, category, description, created_at",
        [title, price, category, description],
    )
    return jsonify(ok=True, item=_row_to_item(row)), 201


@app.get("/items/<int:item_id>")
def get_item(item_id):
    row = myapp_db.queryone(
        "SELECT id, title, price, category, description, created_at FROM items WHERE id = %s",
        [item_id],
    )
    if not row:
        return jsonify(ok=False, error="商品不存在"), 404
    return jsonify(ok=True, item=_row_to_item(row))


@app.delete("/items/<int:item_id>")
def delete_item(item_id):
    n = myapp_db.execute("DELETE FROM items WHERE id = %s", [item_id])
    if not n:
        return jsonify(ok=False, error="商品不存在"), 404
    return jsonify(ok=True, deleted=item_id)


@app.get("/stats")
def stats():
    row = myapp_db.queryone(
        "SELECT COUNT(*)::int AS total, "
        "COALESCE(SUM(price), 0)::float AS total_value, "
        "COUNT(DISTINCT category)::int AS categories FROM items"
    )
    return jsonify(
        ok=True,
        total=row["total"] if row else 0,
        total_value=float(row["total_value"]) if row else 0.0,
        categories=row["categories"] if row else 0,
        time=_now_iso(),
    )
