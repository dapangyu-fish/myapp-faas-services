from flask import Flask, jsonify, request

app = Flask(__name__)


def _base(method, path):
    return {
        "ok": True,
        "method": method,
        "path": path,
        "service": "http-validator",
        "headers": {k: v for k, v in request.headers.items()},
        "query": request.args.to_dict(flat=True),
        "body": request.get_json(silent=True),
    }


def _final(payload, status=200):
    payload["raw"] = payload
    return jsonify(payload), status


@app.get("/ping")
def ping():
    payload = _base("GET", "/ping")
    payload["message"] = "pong"
    payload["fixed"] = {"echo": True, "version": "1.0.0"}
    return _final(payload, 200)


@app.get("/echo")
def echo():
    payload = _base("GET", "/echo")
    payload["echo"] = payload["query"]
    return _final(payload, 200)


@app.post("/users")
def create_user():
    payload = _base("POST", "/users")
    body = payload["body"] or {}
    payload["created"] = {
        "id": 1001,
        "name": body.get("name", ""),
        "email": body.get("email", ""),
        "age": body.get("age", 0),
    }
    return _final(payload, 201)


@app.put("/users/<user_id>")
def replace_user(user_id):
    payload = _base("PUT", f"/users/{user_id}")
    body = payload["body"] or {}
    payload["replaced"] = {
        "id": user_id,
        "name": body.get("name", ""),
        "email": body.get("email", ""),
    }
    return _final(payload, 200)


@app.patch("/users/<user_id>")
def patch_user(user_id):
    payload = _base("PATCH", f"/users/{user_id}")
    body = payload["body"] or {}
    payload["patched"] = {"id": user_id, "fields": list(body.keys())}
    return _final(payload, 200)


@app.delete("/users/<user_id>")
def delete_user(user_id):
    payload = _base("DELETE", f"/users/{user_id}")
    payload["deleted"] = {"id": user_id}
    return _final(payload, 200)


@app.get("/headers")
def headers():
    payload = _base("GET", "/headers")
    payload["response_headers"] = {
        "X-Validator-Service": "http-validator",
        "X-Supported-Methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS",
    }
    payload["received_header_count"] = len(request.headers)
    return _final(payload, 200)


@app.options("/capabilities")
def capabilities():
    payload = _base("OPTIONS", "/capabilities")
    payload["allow"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    payload["x_validator_service"] = "http-validator"
    return _final(payload, 204)


if __name__ == "__main__":
    app.run()
