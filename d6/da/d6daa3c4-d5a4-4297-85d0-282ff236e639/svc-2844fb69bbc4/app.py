from flask import Flask, jsonify, request
app = Flask(__name__)

@app.get("/expenses")
def list_expenses():
    return jsonify({"expenses": [], "total": 0, "count": 0})

@app.post("/expenses")
def create_expense():
    body = request.get_json(silent=True) or {}
    return jsonify({"id": "1", "amount": float(body.get("amount", 0)), "category": body.get("category", ""), "note": body.get("note", ""), "created_at": ""}), 201
