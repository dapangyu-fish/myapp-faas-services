"""小红书风格「笔记 + 评论 + 点赞」FaaS 后端。

身份：myapp_auth.current_user() = 当前调用者的组内假名（已验证、不可伪造）。
公开内容用 myapp_db 裸 SQL（人人可读）；写入把 author/owner 强制成当前用户的假名，
所以谁都改不了别人的笔记/评论/显示名。显示名由客户端用真实平台昵称同步进 profiles。
值一律用 %s 占位（禁 f-string 拼 SQL）。
"""
from flask import Flask, request, jsonify
import myapp_db
import myapp_auth

app = Flask(__name__)

INDENT_PX = 16          # 每层楼中楼缩进像素
INDENT_CAP = 10         # 视觉缩进封顶防溢出
COLLAPSE_AFTER = 2      # 一组楼中楼超过 2 条默认收起


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
    row = myapp_db.queryone("SELECT display_name FROM profiles WHERE owner_id = %s", [owner_id])
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
    return jsonify({"ok": True})


# ── 笔记（posts）──

@app.get("/feed")
def list_feed():
    """全站笔记流（按时间倒序，带作者昵称、点赞/评论数、liked_by_me）。"""
    me = _me()
    rows = myapp_db.query(
        "SELECT po.id, po.author_id, po.title, po.body, po.like_count, po.comment_count, po.created_at, "
        "       COALESCE(p.display_name,'') AS author_name, "
        "       EXISTS (SELECT 1 FROM post_likes l WHERE l.post_id = po.id AND l.user_id = %s) AS liked_by_me "
        "FROM posts po LEFT JOIN profiles p ON p.owner_id = po.author_id "
        "ORDER BY po.created_at DESC LIMIT 200",
        [me or ""],
    )
    return jsonify({"posts": rows})


@app.get("/my-posts")
def my_posts():
    """当前用户发过的笔记（公开读，需登录以确认身份）。"""
    me = _me()
    if not me:
        return _need_login()
    rows = myapp_db.query(
        "SELECT po.id, po.author_id, po.title, po.body, po.like_count, po.comment_count, po.created_at, "
        "       COALESCE(p.display_name,'') AS author_name, "
        "       EXISTS (SELECT 1 FROM post_likes l WHERE l.post_id = po.id AND l.user_id = %s) AS liked_by_me "
        "FROM posts po LEFT JOIN profiles p ON p.owner_id = po.author_id "
        "WHERE po.author_id = %s ORDER BY po.created_at DESC LIMIT 200",
        [me, me],
    )
    return jsonify({"posts": rows})


@app.post("/posts")
def create_post():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    title = str(body.get("title") or "").strip()[:120]
    text = str(body.get("body") or "").strip()[:5000]
    if not title:
        return jsonify({"error": "标题必填"}), 400
    if not text:
        return jsonify({"error": "正文必填"}), 400
    _sync_name(me, body)
    row = myapp_db.queryone(
        "INSERT INTO posts (author_id, title, body) VALUES (%s, %s, %s) "
        "RETURNING id, title, body, like_count, comment_count, created_at",
        [me, title, text],
    )
    row["author_name"] = _name_of(me)
    row["liked_by_me"] = False
    return jsonify({"post": row})


@app.delete("/posts")
def delete_post():
    me = _me()
    if not me:
        return _need_login()
    pid = str(request.args.get("post_id") or "").strip()
    if not pid:
        return jsonify({"error": "缺少 post_id"}), 400
    # 只能删自己的笔记（命中 0 行 → 403）
    n = myapp_db.execute("DELETE FROM posts WHERE id = %s AND author_id = %s", [pid, me])
    if not n:
        return jsonify({"error": "无权删除或不存在"}), 403
    # 顺手清理点赞 + 评论
    myapp_db.execute("DELETE FROM post_likes WHERE post_id = %s", [pid])
    myapp_db.execute("DELETE FROM comments WHERE post_id = %s", [pid])
    return jsonify({"ok": True})


@app.get("/post")
def get_post():
    """单篇笔记详情 + 评论（DFS 拍平、带 depth/indent/kind，按 expanded 折叠楼中楼）。"""
    pid = str(request.args.get("post_id") or "").strip()
    expanded = [x for x in str(request.args.get("expanded") or "").split(",") if x]
    me = _me()
    t = myapp_db.queryone(
        "SELECT po.id, po.author_id, po.title, po.body, po.like_count, po.comment_count, po.created_at, "
        "       COALESCE(p.display_name,'') AS author_name, "
        "       EXISTS (SELECT 1 FROM post_likes l WHERE l.post_id = po.id AND l.user_id = %s) AS liked_by_me "
        "FROM posts po LEFT JOIN profiles p ON p.owner_id = po.author_id WHERE po.id = %s",
        [me or "", pid],
    )
    if not t:
        return jsonify({"error": "笔记不存在"}), 404
    rows = myapp_db.query(
        "SELECT c.id, c.parent_id, c.body, c.created_at, c.author_id, "
        "       COALESCE(p.display_name,'') AS author_name "
        "FROM comments c LEFT JOIN profiles p ON p.owner_id = c.author_id "
        "WHERE c.post_id = %s ORDER BY c.created_at ASC LIMIT 2000",
        [pid],
    )
    return jsonify({"post": t, "comments": _flatten_comments(rows, expanded, me)})


# ── 评论 ──

def _flatten_comments(rows, expanded, me):
    """和贴吧同款：先序 DFS 拍平、按 depth 设 indent，超过 2 条默认折叠。"""
    expanded = set(expanded or [])
    children = {}
    for r in rows:
        children.setdefault(r.get("parent_id"), []).append(r)

    def frames_for(parent_id, depth, is_root):
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
    stack = list(reversed(frames_for(None, 0, True)))
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
            node["is_root"] = (depth == 0)
            node["is_me"] = (me and node.get("author_id") == me)
            node["floor_label"] = "评论" if depth == 0 else "回复"
            ordered.append(node)
            for cf in reversed(frames_for(nid, depth + 1, False)):
                stack.append(cf)
        else:
            parent_id = f[1]
            depth = f[2]
            cap = depth if depth < INDENT_CAP else INDENT_CAP
            marker = {
                "id": kind + "-" + str(parent_id), "kind": kind, "parent_id": parent_id,
                "depth": cap, "indent": cap * INDENT_PX, "is_root": False, "is_me": False,
                "author_id": "", "author_name": "", "body": "", "created_at": None,
            }
            if kind == "more":
                marker["remaining"] = f[3]
            ordered.append(marker)
    return ordered


@app.post("/comments")
def create_comment():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    pid = str(body.get("post_id") or "").strip()
    text = str(body.get("body") or "").strip()[:2000]
    if not pid or not text:
        return jsonify({"error": "内容和笔记必填"}), 400
    _sync_name(me, body)
    if not myapp_db.queryone("SELECT id FROM posts WHERE id = %s", [pid]):
        return jsonify({"error": "笔记不存在"}), 404
    parent = str(body.get("parent_id") or "").strip() or None
    if parent and not myapp_db.queryone("SELECT id FROM comments WHERE id = %s AND post_id = %s", [parent, pid]):
        return jsonify({"error": "回复目标不存在"}), 404
    row = myapp_db.queryone(
        "INSERT INTO comments (post_id, parent_id, author_id, body) VALUES (%s, %s, %s, %s) "
        "RETURNING id, parent_id, body, created_at",
        [pid, parent, me, text],
    )
    myapp_db.execute("UPDATE posts SET comment_count = comment_count + 1 WHERE id = %s", [pid])
    row["author_name"] = _name_of(me)
    row["is_me"] = True
    row["is_root"] = not parent
    row["kind"] = "post"
    row["depth"] = 0 if not parent else 1
    row["indent"] = row["depth"] * INDENT_PX
    row["floor_label"] = "评论" if not parent else "回复"
    return jsonify({"comment": row})


@app.delete("/comments")
def delete_comment():
    me = _me()
    if not me:
        return _need_login()
    cid = str(request.args.get("comment_id") or "").strip()
    # 找到这条评论所属笔记（用于更新 comment_count）
    row = myapp_db.queryone("SELECT post_id FROM comments WHERE id = %s AND author_id = %s", [cid, me])
    if not row:
        return jsonify({"error": "无权删除或不存在"}), 403
    post_id = row["post_id"]
    myapp_db.execute("DELETE FROM comments WHERE id = %s", [cid])
    myapp_db.execute(
        "UPDATE posts SET comment_count = GREATEST(0, comment_count - 1) WHERE id = %s",
        [post_id],
    )
    return jsonify({"ok": True})


# ── 点赞 ──

@app.post("/like")
def toggle_like():
    me = _me()
    if not me:
        return _need_login()
    body = request.get_json(silent=True) or {}
    pid = str(body.get("post_id") or "").strip()
    if not pid:
        return jsonify({"error": "缺少 post_id"}), 400
    if not myapp_db.queryone("SELECT id FROM posts WHERE id = %s", [pid]):
        return jsonify({"error": "笔记不存在"}), 404
    existing = myapp_db.queryone(
        "SELECT 1 FROM post_likes WHERE post_id = %s AND user_id = %s", [pid, me]
    )
    if existing:
        myapp_db.execute("DELETE FROM post_likes WHERE post_id = %s AND user_id = %s", [pid, me])
        myapp_db.execute(
            "UPDATE posts SET like_count = GREATEST(0, like_count - 1) WHERE id = %s", [pid]
        )
        return jsonify({"liked": False})
    myapp_db.execute(
        "INSERT INTO post_likes (post_id, user_id) VALUES (%s, %s) "
        "ON CONFLICT (post_id, user_id) DO NOTHING",
        [pid, me],
    )
    myapp_db.execute("UPDATE posts SET like_count = like_count + 1 WHERE id = %s", [pid])
    return jsonify({"liked": True})


# ── 用户主页 ──

@app.get("/user")
def get_user():
    """某用户（组内假名）的公开主页：显示名 + 统计 + 最近笔记。"""
    uid = str(request.args.get("owner_id") or "").strip()
    if not uid:
        return jsonify({"error": "缺少 owner_id"}), 400
    stats = myapp_db.queryone(
        "SELECT (SELECT count(*) FROM posts WHERE author_id = %s) AS post_count, "
        "       (SELECT count(*) FROM comments WHERE author_id = %s) AS comment_count",
        [uid, uid],
    ) or {}
    posts = myapp_db.query(
        "SELECT id, title, body, like_count, comment_count, created_at "
        "FROM posts WHERE author_id = %s ORDER BY created_at DESC LIMIT 30",
        [uid],
    )
    me = _me()
    return jsonify({
        "user": {
            "owner_id": uid,
            "display_name": _name_of(uid),
            "post_count": stats.get("post_count", 0),
            "comment_count": stats.get("comment_count", 0),
            "is_self": bool(me and me == uid),
        },
        "posts": posts,
    })
