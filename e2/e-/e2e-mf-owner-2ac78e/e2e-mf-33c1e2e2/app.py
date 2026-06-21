from flask import Flask, jsonify, request
from helpers import square
app = Flask(__name__)
@app.get('/compute')
def compute():
    x = int(request.args.get('x', '0'))
    return jsonify(result=square(x))
