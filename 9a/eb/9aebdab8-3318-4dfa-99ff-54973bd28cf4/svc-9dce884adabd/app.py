from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)


def _now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")


@app.get("/ping")
def ping():
    return jsonify(
        ok=True,
        message="pong",
        service="echo-tester",
        version="1.0.0",
        server_time=_now(),
    )


@app.post("/echo")
def echo():
    body = request.get_json(silent=True) or {}
    text = body.get("text", "")
    if not isinstance(text, str):
        text = str(text)
    received_headers = {}
    for k, v in request.headers.items():
        received_headers[k] = v
    response = jsonify(
        ok=True,
        echoed_text=text,
        echoed_length=len(text),
        received_at=_now(),
        method="POST",
        path="/echo",
        received_headers=received_headers,
        request_body=body,
    )
    response.headers["X-Echo-Service"] = "echo-tester"
    response.headers["X-Echo-Length"] = str(len(text))
    response.headers["X-Server-Time"] = _now()
    return response, 200
