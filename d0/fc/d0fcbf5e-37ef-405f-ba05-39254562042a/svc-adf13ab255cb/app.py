from __future__ import annotations
from datetime import datetime, timezone
from flask import Flask, jsonify, request
import myapp_db

app = Flask(__name__)


def _now_iso():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


@app.get('/messages')
def list_messages():
    rows = myapp_db.query(
        'SELECT id, name, content, created_at FROM messages ORDER BY id DESC LIMIT 200'
    )
    out = []
    for r in rows:
        ts = r.get('created_at')
        if hasattr(ts, 'strftime'):
            ts_s = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            ts_s = str(ts) if ts is not None else ''
        out.append({
            'id': r.get('id'),
            'name': r.get('name') or '',
            'content': r.get('content') or '',
            'time': ts_s,
        })
    return jsonify({'ok': True, 'messages': out, 'count': len(out)})


@app.post('/messages')
def create_message():
    body = request.get_json(silent=True) or {}
    name = (body.get('name') or '').strip()
    content = (body.get('content') or '').strip()
    if not name:
        name = '匿名'
    if not content:
        return jsonify({'ok': False, 'error': 'content is required'}), 400
    if len(name) > 40:
        name = name[:40]
    if len(content) > 2000:
        content = content[:2000]
    row = myapp_db.queryone(
        'INSERT INTO messages(name, content) VALUES (%s, %s) RETURNING id, name, content, created_at',
        [name, content],
    )
    ts = row.get('created_at')
    if hasattr(ts, 'strftime'):
        ts_s = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
    else:
        ts_s = str(ts) if ts is not None else ''
    return jsonify({
        'ok': True,
        'message': {
            'id': row.get('id'),
            'name': row.get('name') or '',
            'content': row.get('content') or '',
            'time': ts_s,
        },
    }), 201
