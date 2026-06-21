"""租房房源后端：CRUD + 筛选查询，Postgres 持久化。"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, request

import myapp_db

app = Flask(__name__)

ROOM_TYPES = ["整层", "套房", "雅房"]


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_listing(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "region": row["region"],
        "monthly_rent": row["monthly_rent"],
        "room_type": row["room_type"],
        "ping_size": float(row["ping_size"]) if row["ping_size"] is not None else None,
        "description": row["description"] or "",
        "is_rented": bool(row["is_rented"]),
        "created_at": row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["created_at"] else None,
    }


@app.get("/listings")
def list_listings():
    region = (request.args.get("region") or "").strip()
    min_rent_str = (request.args.get("min_rent") or "").strip()
    max_rent_str = (request.args.get("max_rent") or "").strip()
    room_type = (request.args.get("room_type") or "").strip()
    show_rented_str = (request.args.get("show_rented") or "").strip()

    sql = "SELECT id, title, region, monthly_rent, room_type, ping_size, description, is_rented, created_at FROM listings"
    where = []
    params = []

    if region:
        where.append("region = %s")
        params.append(region)
    if min_rent_str:
        try:
            min_rent = int(min_rent_str)
            where.append("monthly_rent >= %s")
            params.append(min_rent)
        except ValueError:
            pass
    if max_rent_str:
        try:
            max_rent = int(max_rent_str)
            where.append("monthly_rent <= %s")
            params.append(max_rent)
        except ValueError:
            pass
    if room_type and room_type in ROOM_TYPES:
        where.append("room_type = %s")
        params.append(room_type)
    if show_rented_str == "1":
        pass  # show all including rented
    else:
        where.append("is_rented = FALSE")

    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT 200"

    rows = myapp_db.query(sql, params)
    listings = [_row_to_listing(r) for r in rows]
    return jsonify(ok=True, listings=listings, count=len(listings), time=_now_iso())


@app.post("/listings")
def create_listing():
    body = request.get_json(silent=True) or {}
    title = (body.get("title") or "").strip()
    if not title:
        return jsonify(ok=False, error="标题不能为空"), 400
    region = (body.get("region") or "").strip()
    if not region:
        return jsonify(ok=False, error="地区不能为空"), 400
    try:
        monthly_rent = int(body.get("monthly_rent") or 0)
    except (TypeError, ValueError):
        return jsonify(ok=False, error="月租金必须为整数"), 400
    if monthly_rent <= 0:
        return jsonify(ok=False, error="月租金必须大于 0"), 400
    room_type = (body.get("room_type") or "").strip()
    if room_type not in ROOM_TYPES:
        return jsonify(ok=False, error="房型必须为 整层/套房/雅房 之一"), 400
    try:
        ping_size = float(body.get("ping_size") or 0)
    except (TypeError, ValueError):
        ping_size = None
    description = (body.get("description") or "").strip()

    row = myapp_db.queryone(
        "INSERT INTO listings(title, region, monthly_rent, room_type, ping_size, description) "
        "VALUES (%s, %s, %s, %s, %s, %s) "
        "RETURNING id, title, region, monthly_rent, room_type, ping_size, description, is_rented, created_at",
        [title, region, monthly_rent, room_type, ping_size, description],
    )
    return jsonify(ok=True, listing=_row_to_listing(row)), 201


@app.get("/listings/<int:listing_id>")
def get_listing(listing_id):
    row = myapp_db.queryone(
        "SELECT id, title, region, monthly_rent, room_type, ping_size, description, is_rented, created_at FROM listings WHERE id = %s",
        [listing_id],
    )
    if not row:
        return jsonify(ok=False, error="房源不存在"), 404
    return jsonify(ok=True, listing=_row_to_listing(row))


@app.put("/listings/<int:listing_id>/rent")
def toggle_rented(listing_id):
    body = request.get_json(silent=True) or {}
    is_rented = bool(body.get("is_rented", True))
    row = myapp_db.queryone(
        "UPDATE listings SET is_rented = %s WHERE id = %s "
        "RETURNING id, title, region, monthly_rent, room_type, ping_size, description, is_rented, created_at",
        [is_rented, listing_id],
    )
    if not row:
        return jsonify(ok=False, error="房源不存在"), 404
    return jsonify(ok=True, listing=_row_to_listing(row))


@app.delete("/listings/<int:listing_id>")
def delete_listing(listing_id):
    n = myapp_db.execute("DELETE FROM listings WHERE id = %s", [listing_id])
    if not n:
        return jsonify(ok=False, error="房源不存在"), 404
    return jsonify(ok=True, deleted=listing_id)


@app.get("/regions")
def list_regions():
    rows = myapp_db.query("SELECT DISTINCT region FROM listings WHERE is_rented = FALSE ORDER BY region")
    regions = [r["region"] for r in rows]
    return jsonify(ok=True, regions=regions, count=len(regions))
