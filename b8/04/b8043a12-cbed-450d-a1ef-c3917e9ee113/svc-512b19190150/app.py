from __future__ import annotations
from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


@app.get('/notes')
def list_notes():
    rows = myapp_db.query(
        'SELECT id, title, body, created_at FROM notes ORDER BY id DESC'
    )
    items = []
    for r in rows:
        items.append({
            'id': r['id'],
            'title': r['title'],
            'body': r['body'],
            'created_at': r['created_at'].isoformat() if r.get('created_at') else None,
        })
    return jsonify({'ok': True, 'items': items})


@app.post('/notes')
def create_note():
    body = request.get_json(silent=True) or {}
    title = (body.get('title') or '').strip()
    note_body = body.get('body') or ''
    if not title:
        return jsonify({'ok': False, 'error': '标题不能为空'}), 400
    row = myapp_db.queryone(
        'INSERT INTO notes(title, body) VALUES (%s, %s) '
        'RETURNING id, title, body, created_at',
        [title, note_body]
    )
    return jsonify({
        'ok': True,
        'item': {
            'id': row['id'],
            'title': row['title'],
            'body': row['body'],
            'created_at': row['created_at'].isoformat() if row.get('created_at') else None,
        }
    }), 201


@app.delete('/notes/<note_id>')
def delete_note(note_id):
    try:
        nid = int(note_id)
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': '无效id'}), 400
    n = myapp_db.execute('DELETE FROM notes WHERE id = %s', [nid])
    return jsonify({'ok': True, 'deleted': n})
