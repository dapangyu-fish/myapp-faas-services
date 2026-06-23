"""打卡社区 FaaS 后端：发布打卡 / 时间线 / 详情 / 点赞 / 评论 / 我的。

身份：myapp_auth.current_user() = 组内假名（不可伪造）。
公开读用 myapp_db 裸 SQL；写入强制 author_id = me，所以谁都改不了别人的内容。
显示名（display_name）由客户端用真实平台昵称同步进 profiles 表，列表 JOIN 出来。
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
    name = str((body or {}).get("display_name") or "").strip()[:64]
    if me and name:
        myapp_db.execute(
            "INSERT INTO profiles (owner_id, display_name, updated_at) "
            "VALUES (%s, %s, now()) "
            "ON CONFLICT (owner_id) DO UPDATE SET "
            "display_name = EXCLUDED.display_name, updated_at = now()",
            [me, name],
        )


def _name_of(owner_id):
    if not owner_id:
        return ""
    row = myapp_db.queryone(
        "SELECT display_name FROM profiles WHERE owner_id = %s",
        [owner_id],
    )
    return (row or {}).get("display_name", "") or ""


def _decorate(row, me):
    """给一行 checkin 补 is_mine / liked_by_me / like_label / created_label。"""
    cid = row.get("id")
    row["is_mine"] = bool(me) and (row.get("author_id") == me)
    liked = False
    if me:
        liked = bool(myapp_db.queryone(
            "SELECT 1 FROM likes WHERE checkin_id = %s AND owner_id = %s LIMIT 1",
            [cid, me],
        ))
    row["liked_by_me"] = liked
    row["like_label"] = "已赞" if liked else "点赞"
    created = row.get("created_at")
    row["created_label"] = str(created)[:19] if created else ""
    return row


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
    return jsonify({"ok": True})


@app.get("/feed")
def feed():
    me = _me()
    rows = myapp_db.query(
        "SELECT c.id, c.author_id, c.content, c.like_count, c.comment_count, c.created_at, "
        "COALESCE(p.display_name, '') AS author_name "
        "FROM checkins c LEFT JOIN profiles p ON p.owner_id = c.author_id "
        "ORDER BY c.created_at DESC LIMIT 200",
    )
    for r in rows:
        _decorate(r, me)
    return jsonify({"checkins": rows})


@app.post("/checkins")
def create_checkin():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    content = str(body.get("content") or "").strip()[:2000]
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO checkins (author_id, content) VALUES (%s, %s) "
        "RETURNING id, author_id, content, like_count, comment_count, created_at",
        [me, content],
    )
    row["author_name"] = _name_of(me)
    _decorate(row, me)
    return jsonify({"checkin": row})


@app.route("/checkins/<checkin_id>", methods=["DELETE"])
def delete_checkin(checkin_id):
    me = _me()
    if not me:
        return _need_login()
    n = myapp_db.execute(
        "DELETE FROM checkins WHERE id = %s AND author_id = %s",
        [checkin_id, me],
    )
    if not n:
        return jsonify({"error": "无权删除或不存在"}), 403
    myapp_db.execute("DELETE FROM likes WHERE checkin_id = %s", [checkin_id])
    myapp_db.execute("DELETE FROM comments WHERE checkin_id = %s", [checkin_id])
    return jsonify({"ok": True})


@app.get("/checkin")
def get_checkin():
    me = _me()
    cid = str(request.args.get("checkin_id") or "").strip()
    if not cid:
        return jsonify({"error": "缺少 checkin_id"}), 400
    row = myapp_db.queryone(
        "SELECT c.id, c.author_id, c.content, c.like_count, c.comment_count, c.created_at, "
        "COALESCE(p.display_name, '') AS author_name "
        "FROM checkins c LEFT JOIN profiles p ON p.owner_id = c.author_id "
        "WHERE c.id = %s",
        [cid],
    )
    if not row:
        return jsonify({"error": "打卡不存在"}), 404
    _decorate(row, me)
    comments = myapp_db.query(
        "SELECT cm.id, cm.author_id, cm.body, cm.created_at, "
        "COALESCE(p.display_name, '') AS author_name "
        "FROM comments cm LEFT JOIN profiles p ON p.owner_id = cm.author_id "
        "WHERE cm.checkin_id = %s ORDER BY cm.created_at ASC LIMIT 500",
        [cid],
    )
    for c in comments:
        ct = c.get("created_at")
        c["created_label"] = str(ct)[:19] if ct else ""
    return jsonify({"checkin": row, "comments": comments})


@app.post("/like")
def toggle_like():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    cid = str(body.get("checkin_id") or "").strip()
    if not cid:
        return jsonify({"error": "缺少 checkin_id"}), 400
    if not myapp_db.queryone("SELECT id FROM checkins WHERE id = %s", [cid]):
        return jsonify({"error": "打卡不存在"}), 404
    existing = myapp_db.queryone(
        "SELECT id FROM likes WHERE checkin_id = %s AND owner_id = %s",
        [cid, me],
    )
    if existing:
        myapp_db.execute("DELETE FROM likes WHERE id = %s", [existing["id"]])
        myapp_db.execute(
            "UPDATE checkins SET like_count = GREATEST(like_count - 1, 0) WHERE id = %s",
            [cid],
        )
        return jsonify({"ok": True, "liked": False})
    myapp_db.execute(
        "INSERT INTO likes (checkin_id, owner_id) VALUES (%s, %s) "
        "ON CONFLICT (checkin_id, owner_id) DO NOTHING",
        [cid, me],
    )
    myapp_db.execute(
        "UPDATE checkins SET like_count = like_count + 1 WHERE id = %s",
        [cid],
    )
    return jsonify({"ok": True, "liked": True})


@app.post("/comments")
def create_comment():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    cid = str(body.get("checkin_id") or "").strip()
    text = str(body.get("body") or "").strip()[:1000]
    if not cid or not text:
        return jsonify({"error": "内容不能为空"}), 400
    _sync_name(me, body)
    if not myapp_db.queryone("SELECT id FROM checkins WHERE id = %s", [cid]):
        return jsonify({"error": "打卡不存在"}), 404
    row = myapp_db.queryone(
        "INSERT INTO comments (checkin_id, author_id, body) VALUES (%s, %s, %s) "
        "RETURNING id, author_id, body, created_at",
        [cid, me, text],
    )
    myapp_db.execute(
        "UPDATE checkins SET comment_count = comment_count + 1 WHERE id = %s",
        [cid],
    )
    row["author_name"] = _name_of(me)
    ct = row.get("created_at")
    row["created_label"] = str(ct)[:19] if ct else ""
    return jsonify({"comment": row})


@app.get("/myfeed")
def myfeed():
    me = _me()
    if not me:
        return _need_login()
    stats_row = myapp_db.queryone(
        "SELECT count(*) AS checkin_count, COALESCE(sum(like_count), 0) AS total_likes "
        "FROM checkins WHERE author_id = %s",
        [me],
    ) or {}
    rows = myapp_db.query(
        "SELECT c.id, c.author_id, c.content, c.like_count, c.comment_count, c.created_at, "
        "COALESCE(p.display_name, '') AS author_name "
        "FROM checkins c LEFT JOIN profiles p ON p.owner_id = c.author_id "
        "WHERE c.author_id = %s ORDER BY c.created_at DESC LIMIT 100",
        [me],
    )
    for r in rows:
        _decorate(r, me)
    return jsonify({
        "stats": {
            "owner_id": me,
            "display_name": _name_of(me),
            "checkin_count": stats_row.get("checkin_count", 0),
            "total_likes": stats_row.get("total_likes", 0),
        },
        "checkins": rows,
    })
