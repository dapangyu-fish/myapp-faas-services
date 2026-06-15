from flask import Flask, jsonify, request

app = Flask(__name__)


@app.post("/sum")
def sum_numbers():
    payload = request.get_json(silent=True) or {}
    a = payload.get("a", 0)
    b = payload.get("b", 0)
    try:
        a_value = float(a)
    except (TypeError, ValueError):
        a_value = 0.0
    try:
        b_value = float(b)
    except (TypeError, ValueError):
        b_value = 0.0
    return jsonify({"result": a_value + b_value})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
