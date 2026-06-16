from flask import Flask, jsonify, request

app = Flask(__name__)


def _coerce_number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number")
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        try:
            if "." in value or "e" in value.lower():
                return float(value)
            return int(value)
        except ValueError:
            raise ValueError(f"{field} must be a number")
    raise ValueError(f"{field} must be a number")


@app.post("/sum")
def sum_handler():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400
    if "a" not in payload or "b" not in payload:
        return jsonify({"error": "both 'a' and 'b' are required"}), 400
    try:
        a = _coerce_number(payload.get("a"), "a")
        b = _coerce_number(payload.get("b"), "b")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"result": a + b})


@app.get("/health")
def health():
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
