from flask import Flask, jsonify, request
import myapp_db
app = Flask(__name__)
@app.get('/todos')
def list_todos():
    return jsonify(myapp_db.query('SELECT id, title, done FROM todos ORDER BY id'))
@app.post('/todos')
def add_todo():
    body = request.get_json(silent=True) or {}
    title = (body.get('title') or '').strip()
    if not title:
        return jsonify(error='title required'), 400
    row = myapp_db.queryone('INSERT INTO todos(title) VALUES (%s) RETURNING id, title, done', [title])
    return jsonify(row), 201
@app.get('/count')
def count():
    return jsonify(myapp_db.queryone('SELECT count(*) AS n FROM todos'))
