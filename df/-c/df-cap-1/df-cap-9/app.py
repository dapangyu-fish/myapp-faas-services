from flask import Flask, jsonify
app = Flask(__name__)
@app.get('/ping')
def ping():
    return jsonify(ok=True, n=9)
