"""多用户论坛后端：公开主题帖 + 评论 + 用户显示名。

身份：myapp_auth.current_user() = 当前调用者的组内假名（不可伪造，按服务组隔离）。
公开内容（帖子、评论）人人可读；写入把 author_id 强制成当前用户的假名，
所以谁都改不了/冒充不了别人的帖子。显示名由前端用真实平台昵称同步进 profiles。
所有 SQL 一律 %s 占位（禁 f-string 拼 SQL 防注入）。
"""
from flask import Flask, request, jsonify
import myapp_db
import myapp_auth

app = Flask(__name__)


def _me():
    return myapp_auth.current_user()


def _need_login():
    return jsonify({"error": "login required"}), 401


def _sync_name(me, body):
    """把调用者自报的真实昵称写进自己的 profiles 行（只能改自己的）。"""
    name = str((body or {}).get("display_name") or "").strip()[:64]
    if me and name:
        myapp_db.execute(
            "INSERT INTO profiles (owner_id, display_name, updated_at) VALUES (%s, %s, now()) "
            "ON CONFLICT (owner_id) DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = now()",
            [me, name],
        )


def _name_of(owner_id):
    if not owner_id:
        return ""
    row = myapp_db.queryone(
        "SELECT display_name FROM profiles WHERE owner_id = %s", [owner_id]
    )
    return (row or {}).get("display_name", "") or ""


# ── 身份 ──

@app.get("/whoami")
def whoami():
    me = _me()
    return jsonify({"me": me or "", "display_name": _name_of(me), "logged_in": bool(me)})


@app.post("/me")
def set_me():
    me = _me()
    if not me:
        return _need_login()
    _sync_name(me, request.get_json(silent=True) or {})
    return jsonify({"ok": True, "me": me, "display_name": _name_of(me)})


# ── 主题帖 ──

@app.get("/threads")
def list_threads():
    """全部主题帖列表（按时间倒序），带作者昵称和评论数。"""
    rows = myapp_db.query(
        "SELECT t.id, t.author_id, t.title, t.body, t.created_at, "
        "COALESCE(p.display_name,'') AS author_name, "
        "(SELECT count(*) FROM comments c WHERE c.thread_id = t.id) AS comment_count "
        "FROM threads t LEFT JOIN profiles p ON p.owner_id = t.author_id "
        "ORDER BY t.created_at DESC LIMIT 200",
    )
    return jsonify({"threads": rows})


@app.post("/threads")
def create_thread():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    title = str(body.get("title") or "").strip()[:120]
    text = str(body.get("body") or "").strip()[:5000]
    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO threads (author_id, title, body) VALUES (%s, %s, %s) "
        "RETURNING id, title, body, created_at",
        [me, title, text],
    )
    row["author_name"] = _name_of(me)
    row["comment_count"] = 0
    return jsonify({"thread": row})


@app.get("/thread")
def get_thread():
    """单个主题 + 评论列表（按时间正序）。"""
    tid = str(request.args.get("thread_id") or "").strip()
    if not tid:
        return jsonify({"error": "缺少 thread_id"}), 400
    t = myapp_db.queryone(
        "SELECT t.id, t.author_id, t.title, t.body, t.created_at, "
        "COALESCE(p.display_name,'') AS author_name "
        "FROM threads t LEFT JOIN profiles p ON p.owner_id = t.author_id "
        "WHERE t.id = %s",
        [tid],
    )
    if not t:
        return jsonify({"error": "帖子不存在"}), 404
    comments = myapp_db.query(
        "SELECT c.id, c.thread_id, c.author_id, c.body, c.created_at, "
        "COALESCE(p.display_name,'') AS author_name "
        "FROM comments c LEFT JOIN profiles p ON p.owner_id = c.author_id "
        "WHERE c.thread_id = %s ORDER BY c.created_at ASC LIMIT 1000",
        [tid],
    )
    return jsonify({"thread": t, "comments": comments})


@app.delete("/threads")
def delete_thread():
    me = _me()
    if not me:
        return _need_login()
    tid = str(request.args.get("thread_id") or "").strip()
    n = myapp_db.execute(
        "DELETE FROM threads WHERE id = %s AND author_id = %s", [tid, me]
    )
    if not n:
        return jsonify({"error": "无权删除或不存在"}), 403
    # 顺手清掉评论（评论也只属于本帖）
    myapp_db.execute("DELETE FROM comments WHERE thread_id = %s", [tid])
    return jsonify({"ok": True})


# ── 评论 ──

@app.post("/comments")
def create_comment():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    tid = str(body.get("thread_id") or "").strip()
    text = str(body.get("body") or "").strip()[:2000]
    if not tid or not text:
        return jsonify({"error": "内容和帖子必填"}), 400
    if not myapp_db.queryone("SELECT id FROM threads WHERE id = %s", [tid]):
        return jsonify({"error": "帖子不存在"}), 404
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO comments (thread_id, author_id, body) VALUES (%s, %s, %s) "
        "RETURNING id, thread_id, body, created_at",
        [tid, me, text],
    )
    row["author_name"] = _name_of(me)
    return jsonify({"comment": row})


@app.delete("/comments")
def delete_comment():
    me = _me()
    if not me:
        return _need_login()
    cid = str(request.args.get("comment_id") or "").strip()
    n = myapp_db.execute(
        "DELETE FROM comments WHERE id = %s AND author_id = %s", [cid, me]
    )
    if not n:
        return jsonify({"error": "无权删除或不存在"}), 403
    return jsonify({"ok": True})


# ── 用户主页（顺便给一个看别人主页的能力）──

@app.get("/user")
def get_user():
    uid = str(request.args.get("owner_id") or "").strip()
    if not uid:
        return jsonify({"error": "缺少 owner_id"}), 400
    me = _me()
    stats = myapp_db.queryone(
        "SELECT (SELECT count(*) FROM threads  WHERE author_id = %s) AS thread_count, "
        "       (SELECT count(*) FROM comments WHERE author_id = %s) AS comment_count",
        [uid, uid],
    ) or {}
    threads = myapp_db.query(
        "SELECT id, title, created_at FROM threads WHERE author_id = %s "
        "ORDER BY created_at DESC LIMIT 30",
        [uid],
    )
    return jsonify({
        "user": {
            "owner_id": uid,
            "display_name": _name_of(uid),
            "thread_count": stats.get("thread_count", 0),
            "comment_count": stats.get("comment_count", 0),
        },
        "threads": threads,
        "is_self": me == uid,
    })