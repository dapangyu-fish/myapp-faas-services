from flask import Flask, jsonify, request

app = Flask(__name__)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


@app.post("/sum")
def sum_numbers():
    payload = request.get_json(silent=True) or {}
    a = payload.get("a")
    b = payload.get("b")
    if not _is_number(a) or not _is_number(b):
        return jsonify({"error": "a and b must be numbers"}), 400
    return jsonify({"result": a + b})


if __name__ == "__main__":
    app.run()
