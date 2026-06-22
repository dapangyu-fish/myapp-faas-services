from __future__ import annotations
from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@app.get("/expenses")
def list_expenses():
    rows = myapp_db.query(
        "SELECT id, amount, note, created_at FROM expenses ORDER BY id DESC LIMIT 500"
    )
    items = []
    total = 0.0
    for row in rows:
        amount = _to_float(row.get("amount"))
        total += amount
        created = row.get("created_at")
        items.append({
            "id": row.get("id"),
            "amount": amount,
            "note": row.get("note") or "",
            "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        })
    # 余额合计仅供前端展示，包含全部历史记录的总额
    total_row = myapp_db.queryone("SELECT COALESCE(SUM(amount), 0) AS total FROM expenses")
    full_total = _to_float(total_row.get("total")) if total_row else total
    return jsonify({"ok": True, "items": items, "total": full_total, "count": len(items)})


@app.post("/expenses")
def create_expense():
    body = request.get_json(silent=True) or {}
    amount = _to_float(body.get("amount"))
    note = (body.get("note") or "").strip()
    if amount <= 0:
        return jsonify({"ok": False, "error": "amount must be > 0"}), 400
    if len(note) > 200:
        note = note[:200]
    row = myapp_db.queryone(
        "INSERT INTO expenses(amount, note) VALUES (%s, %s) "
        "RETURNING id, amount, note, created_at",
        [amount, note],
    )
    created = row.get("created_at") if row else None
    return jsonify({
        "ok": True,
        "item": {
            "id": row.get("id") if row else None,
            "amount": _to_float(row.get("amount")) if row else amount,
            "note": row.get("note") if row else note,
            "created_at": created.isoformat() if hasattr(created, "isoformat") else created,
        }
    }), 201


@app.delete("/expenses/<int:expense_id>")
def delete_expense(expense_id):
    n = myapp_db.execute("DELETE FROM expenses WHERE id = %s", [expense_id])
    return jsonify({"ok": True, "deleted": n})
