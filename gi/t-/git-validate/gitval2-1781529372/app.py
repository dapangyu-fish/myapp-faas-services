from flask import Flask, jsonify, request

app = Flask(__name__)

@app.get("/hello")
def hello():
    name = request.args.get("name", "myapp")
    return jsonify({"ok": True, "message": f"hello {name}"})

@app.get("/headers")
def headers():
    return jsonify({
        "authorization": request.headers.get("Authorization"),
        "cookie": request.headers.get("Cookie"),
        "runtime_token": request.headers.get("X-MyApp-FaaS-Runtime-Token"),
        "user_id": request.headers.get("X-MyApp-User-Id"),
    })
