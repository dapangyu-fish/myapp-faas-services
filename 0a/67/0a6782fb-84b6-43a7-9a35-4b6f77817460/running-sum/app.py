from __future__ import annotations

import re
from typing import Any

from flask import Flask, jsonify, request

app = Flask(__name__)


def _to_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"'{field}' must be a number, got bool")
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            raise ValueError(f"'{field}' must be a number, got empty string")
        if not re.fullmatch(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", text):
            raise ValueError(f"'{field}' must be a number, got {value!r}")
        return float(text)
    raise ValueError(f"'{field}' must be a number")


def _coerce_int(value: float) -> int | float:
    if value.is_integer():
        return int(value)
    return value


@app.post("/sum")
def sum_handler():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "request body must be a JSON object"}), 400
    if "a" not in payload or "b" not in payload:
        return jsonify({"error": "request body must include 'a' and 'b'"}), 400
    try:
        a_value = _to_number(payload["a"], field="a")
        b_value = _to_number(payload["b"], field="b")
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    total = a_value + b_value
    return jsonify({
        "result": _coerce_int(total),
        "a": _coerce_int(a_value),
        "b": _coerce_int(b_value),
    })


if __name__ == "__main__":
    app.run()
