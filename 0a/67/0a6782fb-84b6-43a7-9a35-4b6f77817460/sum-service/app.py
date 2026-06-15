from __future__ import annotations

from flask import Flask, jsonify, request

app = Flask(__name__)


def _coerce_number(value, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a number, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"{field} is empty")
        try:
            return float(text)
        except ValueError as exc:
            raise ValueError(f"{field} is not a valid number: {text}") from exc
    raise ValueError(f"{field} must be a number")


@app.post("/sum")
def sum_endpoint():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400
    if "a" not in payload or "b" not in payload:
        return jsonify({"error": "request body must include 'a' and 'b'"}), 400
    try:
        a = _coerce_number(payload["a"], "a")
        b = _coerce_number(payload["b"], "b")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify({"result": a + b})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
