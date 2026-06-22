from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal
from flask import Flask, jsonify, request

app = Flask(__name__)

_CATEGORIES = ["餐饮", "交通", "购物", "住房", "娱乐", "医疗", "教育", "其他"]

@app.get("/expenses")
def list_expenses():
    import myapp_db
    rows = myapp_db.query(
        "SELECT id, amount, category, note, created_at FROM expenses ORDER BY created_at DESC LIMIT 200"
    )
    items = []
    for r in rows:
        items.append({
            "id": str(r[0]),
            "amount": float(r[1]) if r[1] is not None else 0,
            "category": r[2] or "",
            "note": r[3] or "",
            "created_at": r[4].isoformat() if r[4] is not None else ""
        })
    total = 0.0
    for it in items:
        total += it["amount"]
    return jsonify({"expenses": items, "total": round(total, 2), "count": len(items)})

@app.post("/expenses")
def create_expense():
    import myapp_db
    body = request.get_json(silent=True) or {}
    amount = body.get("amount", 0)
    category = body.get("category", "其他")
    note = body.get("note", "")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify(error="金额必须为数字"), 400
    if amount <= 0:
        return jsonify(error="金额必须大于 0"), 400
    if category not in _CATEGORIES:
        category = "其他"
    note = str(note)[:200]
    row = myapp_db.queryone(
        "INSERT INTO expenses(amount, category, note) VALUES (%s, %s, %s) "
        "RETURNING id, amount, category, note, created_at",
        [amount, category, note]
    )
    return jsonify({
        "id": str(row[0]),
        "amount": float(row[1]),
        "category": row[2],
        "note": row[3],
        "created_at": row[4].isoformat()
    }), 201
