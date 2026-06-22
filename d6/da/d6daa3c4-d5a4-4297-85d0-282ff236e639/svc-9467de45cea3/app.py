from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


@app.get("/expenses")
def list_expenses():
    rows = myapp_db.query(
        "SELECT id, amount, category, note, created_at FROM expenses ORDER BY id DESC"
    )
    return jsonify(
        [
            {
                "id": r[0],
                "amount": float(r[1]),
                "category": r[2],
                "note": r[3],
                "created_at": r[4].isoformat() if r[4] else None,
            }
            for r in rows
        ]
    )


@app.post("/expenses")
def create_expense():
    body = request.get_json(silent=True) or {}
    amount = float(body.get("amount", 0))
    category = str(body.get("category", ""))
    note = str(body.get("note", ""))
    row = myapp_db.queryone(
        "INSERT INTO expenses(amount, category, note) VALUES (%s,%s,%s) "
        "RETURNING id, amount, category, note, created_at",
        [amount, category, note],
    )
    return (
        jsonify(
            {
                "id": row[0],
                "amount": float(row[1]),
                "category": row[2],
                "note": row[3],
                "created_at": row[4].isoformat() if row[4] else None,
            }
        ),
        201,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
