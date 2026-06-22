from flask import Flask, jsonify, request
import myapp_db
app = Flask(__name__)

@app.get("/expenses")
def list_expenses():
    rows = myapp_db.query("SELECT id, amount, category, note, created_at FROM expenses ORDER BY created_at DESC LIMIT 200")
    items = []
    for r in rows:
        items.append({
            "id": str(r["id"]),
            "amount": float(r["amount"]) if r["amount"] is not None else 0.0,
            "category": r["category"] or "",
            "note": r["note"] or "",
            "created_at": str(r["created_at"]) if r["created_at"] is not None else ""
        })
    total = sum(it["amount"] for it in items)
    return jsonify({"expenses": items, "total": round(total, 2), "count": len(items)})

@app.post("/expenses")
def create_expense():
    body = request.get_json(silent=True) or {}
    try:
        amount = float(body.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify(error="amount must be a number"), 400
    if amount <= 0:
        return jsonify(error="amount must be > 0"), 400
    category = str(body.get("category", "")).strip() or "其他"
    note = str(body.get("note", ""))[:200]
    row = myapp_db.queryone(
        "INSERT INTO expenses(amount, category, note) VALUES (%s, %s, %s) RETURNING id, amount, category, note, created_at",
        [amount, category, note]
    )
    return jsonify({
        "id": str(row["id"]),
        "amount": float(row["amount"]),
        "category": row["category"],
        "note": row["note"],
        "created_at": str(row["created_at"])
    }), 201
