from flask import Flask, jsonify, request
import myapp_db
app = Flask(__name__)
@app.get('/notes')
def ls():
    return jsonify(myapp_db.query('SELECT id, body FROM notes ORDER BY id'))
@app.post('/notes')
def add():
    b=(request.get_json(silent=True) or {}).get('body','')
    return jsonify(myapp_db.queryone('INSERT INTO notes(body) VALUES (%s) RETURNING id, body',[b])),201
