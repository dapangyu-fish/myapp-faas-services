from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/sum")
def sum_numbers():
    payload = request.get_json(silent=True) or {}
    a = payload.get("a")
    b = payload.get("b")
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        return jsonify({"error": "a and b must be numbers"}), 400
    return jsonify({"result": a + b})


if __name__ == "__main__":
    app.run()
