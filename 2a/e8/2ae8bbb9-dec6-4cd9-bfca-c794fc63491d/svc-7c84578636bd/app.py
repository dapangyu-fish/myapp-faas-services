"""客服工单系统 FaaS 后端：工单 CRUD + 消息收发 + 未读管理。
身份：myapp_auth.current_user() = 当前调用者的组内假名（已验证、不可伪造）。
工单仅 owner 可见；消息在工单内收发。
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
    """把调用者自报的显示名写进自己的 profiles 行（只能改自己的）。"""
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
    row = myapp_db.queryone("SELECT display_name FROM profiles WHERE owner_id = %s", [owner_id])
    return (row or {}).get("display_name", "") or ""


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


# ── 工单 ──

@app.get("/tickets")
def list_tickets():
    """列出当前用户的工单（按更新时间倒序），带最后一条消息预览。"""
    me = _me()
    if not me:
        return _need_login()
    rows = myapp_db.query(
        "SELECT t.id, t.title, t.description, t.status, t.unread_count, t.last_message_at, "
        "t.created_at, t.updated_at, "
        "(SELECT m.body FROM messages m WHERE m.ticket_id = t.id ORDER BY m.created_at DESC LIMIT 1) AS last_msg "
        "FROM tickets t WHERE t.owner_id = %s ORDER BY t.updated_at DESC LIMIT 100",
        [me],
    )
    return jsonify({"tickets": rows})


@app.post("/tickets")
def create_ticket():
    """创建工单。title 必填，description 选填。"""
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    title = str(body.get("title") or "").strip()[:120]
    if not title:
        return jsonify({"error": "标题不能为空"}), 400
    desc = str(body.get("description") or "").strip()[:2000]
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO tickets (owner_id, title, description) VALUES (%s, %s, %s) "
        "RETURNING id, title, description, status, unread_count, created_at, updated_at",
        [me, title, desc],
    )
    return jsonify({"ticket": row}), 201


@app.get("/tickets/<ticket_id>")
def get_ticket(ticket_id):
    """获取工单详情 + 全部消息（按时间正序）。仅 owner 可看。"""
    me = _me()
    if not me:
        return _need_login()
    t = myapp_db.queryone(
        "SELECT t.id, t.title, t.description, t.status, t.unread_count, t.last_message_at, "
        "t.created_at, t.updated_at FROM tickets t WHERE t.id = %s AND t.owner_id = %s",
        [ticket_id, me],
    )
    if not t:
        return jsonify({"error": "工单不存在"}), 404
    msgs = myapp_db.query(
        "SELECT m.id, m.ticket_id, m.sender_id, m.body, m.created_at, "
        "COALESCE(p.display_name, '') AS sender_name "
        "FROM messages m LEFT JOIN profiles p ON p.owner_id = m.sender_id "
        "WHERE m.ticket_id = %s ORDER BY m.created_at ASC LIMIT 500",
        [ticket_id],
    )
    for m in msgs:
        m["is_me"] = (m.get("sender_id") == me)
    return jsonify({"ticket": t, "messages": msgs})


@app.post("/tickets/<ticket_id>/messages")
def send_message(ticket_id):
    """在工单内发送消息。仅工单 owner 可发。"""
    me = _me()
    if not me:
        return _need_login()
    # 校验工单存在且为当前用户所有
    t = myapp_db.queryone(
        "SELECT id, owner_id, status FROM tickets WHERE id = %s AND owner_id = %s",
        [ticket_id, me],
    )
    if not t:
        return jsonify({"error": "工单不存在"}), 404
    if t["status"] == "closed":
        return jsonify({"error": "工单已关闭，无法发送消息"}), 400
    body = request.get_json(silent=True) or {}
    text = str(body.get("body") or "").strip()[:2000]
    if not text:
        return jsonify({"error": "消息不能为空"}), 400
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO messages (ticket_id, sender_id, body) VALUES (%s, %s, %s) "
        "RETURNING id, ticket_id, sender_id, body, created_at",
        [ticket_id, me, text],
    )
    # 更新工单的未读数（非发送者侧 +1）和最后消息时间
    myapp_db.execute(
        "UPDATE tickets SET unread_count = unread_count + 1, last_message_at = now(), updated_at = now() WHERE id = %s",
        [ticket_id],
    )
    row["is_me"] = True
    row["sender_name"] = _name_of(me)
    return jsonify({"message": row}), 201


@app.put("/tickets/<ticket_id>/read")
def mark_read(ticket_id):
    """标记工单为已读（清零未读数）。"""
    me = _me()
    if not me:
        return _need_login()
    n = myapp_db.execute(
        "UPDATE tickets SET unread_count = 0 WHERE id = %s AND owner_id = %s",
        [ticket_id, me],
    )
    if not n:
        return jsonify({"error": "工单不存在"}), 404
    return jsonify({"ok": True})


@app.put("/tickets/<ticket_id>/close")
def close_ticket(ticket_id):
    """关闭工单。"""
    me = _me()
    if not me:
        return _need_login()
    n = myapp_db.execute(
        "UPDATE tickets SET status = 'closed', updated_at = now() WHERE id = %s AND owner_id = %s",
        [ticket_id, me],
    )
    if not n:
        return jsonify({"error": "工单不存在"}), 404
    return jsonify({"ok": True})
