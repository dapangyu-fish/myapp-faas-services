import time
import uuid
from flask import Flask, request, jsonify

app = Flask(__name__)

todos = []


def _find(todo_id):
    for t in todos:
        if t['id'] == todo_id:
            return t
    return None


@app.get('/todos')
def list_todos():
    return jsonify({'todos': todos})


@app.post('/todos')
def create_todo():
    data = request.get_json(silent=True) or {}
    todo = {
        'id': str(uuid.uuid4())[:8],
        'title': data.get('title', ''),
        'done': False,
        'created_at': time.strftime('%Y-%m-%d %H:%M')
    }
    todos.insert(0, todo)
    return jsonify({'todo': todo}), 201


@app.get('/todos/<todo_id>')
def get_todo(todo_id):
    t = _find(todo_id)
    if not t:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'todo': t})


@app.put('/todos/<todo_id>')
def update_todo(todo_id):
    t = _find(todo_id)
    if not t:
        return jsonify({'error': 'not found'}), 404
    data = request.get_json(silent=True) or {}
    if 'title' in data:
        t['title'] = data['title']
    if 'done' in data:
        t['done'] = bool(data['done'])
    return jsonify({'todo': t})


@app.delete('/todos/<todo_id>')
def delete_todo(todo_id):
    global todos
    t = _find(todo_id)
    if not t:
        return jsonify({'error': 'not found'}), 404
    todos = [x for x in todos if x['id'] != todo_id]
    return jsonify({'ok': True})


if __name__ == '__main__':
    app.run()
