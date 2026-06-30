"""云社区 论坛后端：板块(zone) / 主题(topic) / 楼中楼回复(reply) + 用户显示名(profile)。

身份：myapp_auth.current_user() = 当前调用者的组内假名（服务端注入、不可伪造）。
公开内容用 myapp_db 裸 SQL（人人可读）；写入把 author/owner 强制成当前用户假名，
谁都改不了别人的帖子/别人的显示名。显示名由客户端用真实平台昵称同步进 profiles。
值一律用 %s 占位（禁 f-string 拼 SQL）。
"""
from flask import Flask, request, jsonify
import myapp_db
import myapp_auth

app = Flask(__name__)

INDENT_PX = 16          # 每层楼中楼缩进像素
INDENT_CAP = 12         # 数据无限层级，视觉缩进封顶防溢出
COLLAPSE_AFTER = 2      # 一组楼中楼超过 2 条默认收起


def _me():
    return myapp_auth.current_user()


def _need_login():
    return jsonify({"error": "请先登录"}), 401


def _sync_name(me, body):
    name = str((body or {}).get("display_name") or "").strip()[:64]
    if me and name:
        myapp_db.execute(
            "INSERT INTO profiles (owner_id, display_name, updated_at) VALUES (%s, %s, now()) "
            "ON CONFLICT (owner_id) DO UPDATE SET display_name = EXCLUDED.display_name, updated_at = now()",
            [me, name])


def _name_of(owner_id):
    if not owner_id:
        return ""
    row = myapp_db.queryone("SELECT display_name FROM profiles WHERE owner_id = %s", [owner_id])
    return (row or {}).get("display_name", "") or ""


@app.get("/whoami")
def whoami():
    me = _me()
    return jsonify({"me": me or "", "display_name": _name_of(me), "logged_in": bool(me)})


@app.post("/profile")
def set_profile():
    me = _me()
    if not me:
        return _need_login()
    _sync_name(me, request.get_json(silent=True) or {})
    return jsonify({"ok": True})


@app.get("/zones")
def list_zones():
    q = str(request.args.get("q") or "").strip()
    base = (
        "SELECT z.id, z.name, z.intro, z.created_at, COALESCE(p.display_name,'') AS owner_name, "
        "(SELECT count(*) FROM topics t WHERE t.zone_id = z.id) AS topic_count "
        "FROM zones z LEFT JOIN profiles p ON p.owner_id = z.owner_id "
    )
    if q:
        rows = myapp_db.query(base + "WHERE z.name ILIKE %s ORDER BY z.created_at DESC LIMIT 100", ["%" + q + "%"])
    else:
        rows = myapp_db.query(base + "ORDER BY z.created_at DESC LIMIT 100")
    return jsonify({"zones": rows})


@app.post("/zones")
def create_zone():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    name = str(body.get("name") or "").strip()[:32]
    if not name:
        return jsonify({"error": "板块名不能为空"}), 400
    _sync_name(me, body)
    if myapp_db.queryone("SELECT id FROM zones WHERE name = %s", [name]):
        return jsonify({"error": "该板块已存在"}), 409
    row = myapp_db.queryone(
        "INSERT INTO zones (name, intro, owner_id) VALUES (%s, %s, %s) RETURNING id, name, intro, created_at",
        [name, str(body.get("intro") or "").strip()[:200], me],
    )
    return jsonify({"zone": row, "is_owner": True})


@app.get("/zone")
def get_zone():
    zid = str(request.args.get("zone_id") or "").strip()
    z = myapp_db.queryone(
        "SELECT z.id, z.name, z.intro, z.owner_id, z.created_at, COALESCE(p.display_name,'') AS owner_name "
        "FROM zones z LEFT JOIN profiles p ON p.owner_id = z.owner_id WHERE z.id = %s",
        [zid],
    )
    if not z:
        return jsonify({"error": "板块不存在"}), 404
    z["is_owner"] = (_me() == z.get("owner_id"))
    return jsonify({"zone": z})


@app.get("/topics")
def list_topics():
    zid = str(request.args.get("zone_id") or "").strip()
    rows = myapp_db.query(
        "SELECT t.id, t.author_id, t.title, t.body, t.reply_count, t.created_at, "
        "COALESCE(p.display_name,'') AS author_name "
        "FROM topics t LEFT JOIN profiles p ON p.owner_id = t.author_id "
        "WHERE t.zone_id = %s ORDER BY t.created_at DESC LIMIT 100",
        [zid],
    )
    return jsonify({"topics": rows})


@app.post("/topics")
def create_topic():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    zid = str(body.get("zone_id") or "").strip()
    title = str(body.get("title") or "").strip()[:120]
    if not zid or not title:
        return jsonify({"error": "板块和标题必填"}), 400
    _sync_name(me, body)
    if not myapp_db.queryone("SELECT id FROM zones WHERE id = %s", [zid]):
        return jsonify({"error": "板块不存在"}), 404
    row = myapp_db.queryone(
        "INSERT INTO topics (zone_id, author_id, title, body) VALUES (%s, %s, %s, %s) "
        "RETURNING id, title, body, created_at",
        [zid, me, title, str(body.get("body") or "").strip()[:5000]],
    )
    return jsonify({"topic": row})


def _flatten(rows, expanded):
    """把楼中楼树形先序拍平成扁平列表（客户端按 indent 缩进渲染）。

    楼层(parent_id NULL)始终全显示；任一组楼中楼 > COLLAPSE_AFTER 且父不在 expanded 里
    → 只显示前 2 条 + kind='more' 行；父在 expanded 里 → 全显示 + kind='collapse' 行。
    迭代式 DFS 避免深栈。"""
    expanded = set(expanded or [])
    children = {}
    for r in rows:
        children.setdefault(r.get("parent_id"), []).append(r)

    def frames(parent_id, depth, is_root):
        kids = children.get(parent_id, [])
        out = []
        show_all = is_root or len(kids) <= COLLAPSE_AFTER or (parent_id in expanded)
        if show_all:
            for k in kids:
                out.append(("node", k, depth))
            if (not is_root) and len(kids) > COLLAPSE_AFTER:
                out.append(("collapse", parent_id, depth))
        else:
            for k in kids[:COLLAPSE_AFTER]:
                out.append(("node", k, depth))
            out.append(("more", parent_id, depth, len(kids) - COLLAPSE_AFTER))
        return out

    ordered, seen = [], set()
    stack = list(reversed(frames(None, 0, True)))
    while stack:
        f = stack.pop()
        kind = f[0]
        if kind == "node":
            _, node, depth = f
            nid = node.get("id")
            if nid in seen:
                continue
            seen.add(nid)
            cap = depth if depth < INDENT_CAP else INDENT_CAP
            node["kind"] = "post"
            node["depth"] = cap
            node["indent"] = cap * INDENT_PX
            node["is_floor"] = (depth == 0)
            node["floor_label"] = "楼层" if depth == 0 else "楼中楼"
            ordered.append(node)
            for cf in reversed(frames(nid, depth + 1, False)):
                stack.append(cf)
        else:
            parent_id = f[1]
            depth = f[2]
            cap = depth if depth < INDENT_CAP else INDENT_CAP
            marker = {
                "id": kind + "-" + str(parent_id), "kind": kind, "parent_id": parent_id,
                "depth": cap, "indent": cap * INDENT_PX,
            }
            if kind == "more":
                marker["remaining"] = f[3]
            ordered.append(marker)
    return ordered


@app.get("/topic")
def get_topic():
    tid = str(request.args.get("topic_id") or "").strip()
    expanded = [x for x in str(request.args.get("expanded") or "").split(",") if x]
    t = myapp_db.queryone(
        "SELECT t.id, t.zone_id, t.title, t.body, t.created_at, t.author_id, "
        "COALESCE(p.display_name,'') AS author_name "
        "FROM topics t LEFT JOIN profiles p ON p.owner_id = t.author_id WHERE t.id = %s",
        [tid],
    )
    if not t:
        return jsonify({"error": "帖子不存在"}), 404
    rows = myapp_db.query(
        "SELECT r.id, r.parent_id, r.body, r.created_at, r.author_id, "
        "COALESCE(p.display_name,'') AS author_name "
        "FROM replies r LEFT JOIN profiles p ON p.owner_id = r.author_id "
        "WHERE r.topic_id = %s ORDER BY r.created_at ASC LIMIT 2000",
        [tid],
    )
    return jsonify({"topic": t, "posts": _flatten(rows, expanded)})


@app.post("/reply")
def create_reply():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    tid = str(body.get("topic_id") or "").strip()
    text = str(body.get("body") or "").strip()[:5000]
    if not tid or not text:
        return jsonify({"error": "内容必填"}), 400
    _sync_name(me, body)
    if not myapp_db.queryone("SELECT id FROM topics WHERE id = %s", [tid]):
        return jsonify({"error": "帖子不存在"}), 404
    parent = str(body.get("parent_id") or "").strip() or None
    if parent and not myapp_db.queryone("SELECT id FROM replies WHERE id = %s AND topic_id = %s", [parent, tid]):
        return jsonify({"error": "回复目标不存在"}), 404
    row = myapp_db.queryone(
        "INSERT INTO replies (topic_id, parent_id, author_id, body) VALUES (%s, %s, %s, %s) "
        "RETURNING id, parent_id, body, created_at",
        [tid, parent, me, text],
    )
    myapp_db.execute("UPDATE topics SET reply_count = reply_count + 1 WHERE id = %s", [tid])
    return jsonify({"post": row})


@app.delete("/reply")
def delete_reply():
    me = _me()
    if not me:
        return _need_login()
    pid = str(request.args.get("post_id") or "").strip()
    n = myapp_db.execute("DELETE FROM replies WHERE id = %s AND author_id = %s", [pid, me])
    if not n:
        return jsonify({"error": "无权删除或不存在"}), 403
    return jsonify({"ok": True})


@app.get("/mine")
def mine():
    me = _me()
    if not me:
        return _need_login()
    stats = myapp_db.queryone(
        "SELECT (SELECT count(*) FROM zones   WHERE owner_id  = %s) AS zone_count, "
        "       (SELECT count(*) FROM topics  WHERE author_id = %s) AS topic_count, "
        "       (SELECT count(*) FROM replies WHERE author_id = %s) AS reply_count",
        [me, me, me],
    ) or {}
    zones = myapp_db.query(
        "SELECT id, name, intro, created_at FROM zones WHERE owner_id = %s ORDER BY created_at DESC LIMIT 30",
        [me],
    )
    topics = myapp_db.query(
        "SELECT t.id, t.title, t.reply_count, t.created_at, t.zone_id, COALESCE(z.name,'') AS zone_name "
        "FROM topics t LEFT JOIN zones z ON z.id = t.zone_id "
        "WHERE t.author_id = %s ORDER BY t.created_at DESC LIMIT 30",
        [me],
    )
    return jsonify({
        "me": {"owner_id": me, "display_name": _name_of(me)},
        "zone_count": stats.get("zone_count", 0),
        "topic_count": stats.get("topic_count", 0),
        "reply_count": stats.get("reply_count", 0),
        "zones": zones, "topics": topics,
    })
