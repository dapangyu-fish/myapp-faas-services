from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/sum")
def sum_numbers():
    payload = request.get_json(silent=True) or {}
    a = payload.get("a", 0)
    b = payload.get("b", 0)
    try:
        result = float(a) + float(b)
    except (TypeError, ValueError):
        return jsonify({"error": "a and b must be numbers"}), 400
    if result.is_integer():
        result = int(result)
    return jsonify({"result": result, "by": "v2"})


if __name__ == "__main__":
    app.run()
