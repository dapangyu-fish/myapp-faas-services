from flask import Flask, jsonify, request
app = Flask(__name__)

@app.get("/expenses")
def list_expenses():
    import myapp_db
    rows = myapp_db.query("SELECT id, amount, category, note, created_at FROM expenses ORDER BY created_at DESC LIMIT 200")
    items = []
    for r in rows:
        items.append({
            "id": str(r[0]),
            "amount": float(r[1]) if r[1] is not None else 0,
            "category": r[2] or "",
            "note": r[3] or "",
            "created_at": str(r[4]) if r[4] is not None else ""
        })
    total = sum(it["amount"] for it in items)
    return jsonify({"expenses": items, "total": round(total, 2), "count": len(items)})

@app.post("/expenses")
def create_expense():
    import myapp_db
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
        "id": str(row[0]),
        "amount": float(row[1]),
        "category": row[2],
        "note": row[3],
        "created_at": str(row[4])
    }), 201
