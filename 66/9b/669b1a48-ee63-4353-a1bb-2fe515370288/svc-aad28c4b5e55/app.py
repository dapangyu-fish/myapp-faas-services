"""外卖点餐后端：餐厅 / 菜品 / 订单 CRUD，Postgres 持久化。"""
from __future__ import annotations

from datetime import datetime, timezone

from flask import Flask, jsonify, request

import myapp_db

app = Flask(__name__)


def _now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _row_to_restaurant(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "name": row["name"],
        "category": row["category"] or "其他",
        "rating": float(row["rating"]) if row["rating"] is not None else 4.5,
        "delivery_fee": float(row["delivery_fee"]) if row["delivery_fee"] is not None else 0.0,
        "delivery_minutes": int(row["delivery_minutes"]) if row["delivery_minutes"] is not None else 30,
        "description": row["description"] or "",
        "emoji": row["emoji"] or "🍱",
        "sales": int(row["sales"]) if row["sales"] is not None else 0,
        "created_at": row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["created_at"] else None,
    }


def _row_to_dish(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "name": row["name"],
        "price": float(row["price"]) if row["price"] is not None else 0.0,
        "description": row["description"] or "",
        "tag": row["tag"] or "",
        "sales": int(row["sales"]) if row["sales"] is not None else 0,
        "created_at": row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["created_at"] else None,
    }


def _row_to_order(row, items=None):
    if row is None:
        return None
    return {
        "id": row["id"],
        "restaurant_id": row["restaurant_id"],
        "restaurant_name": row["restaurant_name"],
        "customer_name": row["customer_name"] or "",
        "phone": row["phone"] or "",
        "address": row["address"] or "",
        "note": row["note"] or "",
        "total_amount": float(row["total_amount"]) if row["total_amount"] is not None else 0.0,
        "status": row["status"] or "待商家接单",
        "created_at": row["created_at"].strftime("%Y-%m-%dT%H:%M:%SZ") if row["created_at"] else None,
        "items": items or [],
    }


def _row_to_order_item(row):
    if row is None:
        return None
    return {
        "id": row["id"],
        "order_id": row["order_id"],
        "dish_id": row["dish_id"],
        "dish_name": row["dish_name"],
        "price": float(row["price"]) if row["price"] is not None else 0.0,
        "quantity": int(row["quantity"]) if row["quantity"] is not None else 0,
    }


# ============ 餐厅 ============

@app.get("/restaurants")
def list_restaurants():
    category = (request.args.get("category") or "").strip()
    query = (request.args.get("q") or "").strip()
    sql = "SELECT id, name, category, rating, delivery_fee, delivery_minutes, description, emoji, sales, created_at FROM restaurants"
    where = []
    params = []
    if category and category not in ("", "全部"):
        where.append("category = %s")
        params.append(category)
    if query:
        where.append("name ILIKE %s")
        params.append("%" + query + "%")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY rating DESC, sales DESC LIMIT 200"
    rows = myapp_db.query(sql, params)
    items = [_row_to_restaurant(r) for r in rows]
    return jsonify(ok=True, restaurants=items, count=len(items), time=_now_iso())


@app.get("/restaurants/<int:rid>")
def get_restaurant(rid):
    row = myapp_db.queryone(
        "SELECT id, name, category, rating, delivery_fee, delivery_minutes, description, emoji, sales, created_at "
        "FROM restaurants WHERE id = %s",
        [rid],
    )
    if not row:
        return jsonify(ok=False, error="餐厅不存在"), 404
    return jsonify(ok=True, restaurant=_row_to_restaurant(row))


@app.get("/restaurants/<int:rid>/menu")
def get_restaurant_menu(rid):
    rest = myapp_db.queryone(
        "SELECT id, name, category, rating, delivery_fee, delivery_minutes, description, emoji, sales, created_at "
        "FROM restaurants WHERE id = %s",
        [rid],
    )
    if not rest:
        return jsonify(ok=False, error="餐厅不存在"), 404
    rows = myapp_db.query(
        "SELECT id, restaurant_id, name, price, description, tag, sales, created_at "
        "FROM dishes WHERE restaurant_id = %s ORDER BY sales DESC, id ASC",
        [rid],
    )
    dishes = [_row_to_dish(r) for r in rows]
    return jsonify(ok=True, restaurant=_row_to_restaurant(rest), dishes=dishes, count=len(dishes))


# ============ 菜品 ============

@app.get("/dishes")
def list_dishes():
    restaurant_id = request.args.get("restaurant_id")
    sql = "SELECT id, restaurant_id, name, price, description, tag, sales, created_at FROM dishes"
    params = []
    if restaurant_id:
        sql += " WHERE restaurant_id = %s"
        params.append(int(restaurant_id))
    sql += " ORDER BY sales DESC, id ASC LIMIT 200"
    rows = myapp_db.query(sql, params)
    items = [_row_to_dish(r) for r in rows]
    return jsonify(ok=True, dishes=items, count=len(items))


# ============ 订单 ============

@app.get("/orders")
def list_orders():
    phone = (request.args.get("phone") or "").strip()
    sql = (
        "SELECT id, restaurant_id, restaurant_name, customer_name, phone, address, note, "
        "total_amount, status, created_at FROM orders"
    )
    params = []
    if phone:
        sql += " WHERE phone = %s"
        params.append(phone)
    sql += " ORDER BY id DESC LIMIT 200"
    rows = myapp_db.query(sql, params)
    orders = []
    for r in rows:
        item_rows = myapp_db.query(
            "SELECT id, order_id, dish_id, dish_name, price, quantity FROM order_items "
            "WHERE order_id = %s ORDER BY id ASC",
            [r["id"]],
        )
        orders.append(_row_to_order(r, [_row_to_order_item(it) for it in item_rows]))
    return jsonify(ok=True, orders=orders, count=len(orders), time=_now_iso())


@app.get("/orders/<int:oid>")
def get_order(oid):
    row = myapp_db.queryone(
        "SELECT id, restaurant_id, restaurant_name, customer_name, phone, address, note, "
        "total_amount, status, created_at FROM orders WHERE id = %s",
        [oid],
    )
    if not row:
        return jsonify(ok=False, error="订单不存在"), 404
    item_rows = myapp_db.query(
        "SELECT id, order_id, dish_id, dish_name, price, quantity FROM order_items "
        "WHERE order_id = %s ORDER BY id ASC",
        [oid],
    )
    return jsonify(ok=True, order=_row_to_order(row, [_row_to_order_item(it) for it in item_rows]))


@app.post("/orders")
def create_order():
    body = request.get_json(silent=True) or {}
    restaurant_id = body.get("restaurant_id")
    items_in = body.get("items") or []
    if not restaurant_id or not isinstance(items_in, list) or not items_in:
        return jsonify(ok=False, error="订单缺少餐厅或商品"), 400

    rest = myapp_db.queryone(
        "SELECT id, name, category, rating, delivery_fee, delivery_minutes, description, emoji, sales, created_at "
        "FROM restaurants WHERE id = %s",
        [int(restaurant_id)],
    )
    if not rest:
        return jsonify(ok=False, error="餐厅不存在"), 400

    # 解析并校验商品
    cleaned_items = []
    total = 0.0
    for raw in items_in:
        try:
            dish_id = int(raw.get("dish_id"))
            qty = int(raw.get("quantity") or 0)
        except (TypeError, ValueError):
            return jsonify(ok=False, error="商品参数错误"), 400
        if qty <= 0:
            continue
        dish_row = myapp_db.queryone(
            "SELECT id, restaurant_id, name, price, description, tag, sales, created_at "
            "FROM dishes WHERE id = %s",
            [dish_id],
        )
        if not dish_row:
            return jsonify(ok=False, error="菜品不存在: " + str(dish_id)), 400
        if int(dish_row["restaurant_id"]) != int(restaurant_id):
            return jsonify(ok=False, error="菜品不属于该餐厅: " + dish_row["name"]), 400
        price = float(dish_row["price"])
        total += price * qty
        cleaned_items.append({
            "dish_id": dish_id,
            "dish_name": dish_row["name"],
            "price": price,
            "quantity": qty,
        })

    if not cleaned_items:
        return jsonify(ok=False, error="订单商品为空"), 400

    customer_name = (body.get("customer_name") or "").strip()
    phone = (body.get("phone") or "").strip()
    address = (body.get("address") or "").strip()
    note = (body.get("note") or "").strip()

    new_id = None
    with myapp_db.tx() as cur:
        cur.execute(
            "INSERT INTO orders(restaurant_id, restaurant_name, customer_name, phone, address, note, total_amount, status) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            [int(restaurant_id), rest["name"], customer_name, phone, address, note, total, "待商家接单"],
        )
        new_id = cur.fetchone()["id"]
        for it in cleaned_items:
            cur.execute(
                "INSERT INTO order_items(order_id, dish_id, dish_name, price, quantity) "
                "VALUES (%s, %s, %s, %s, %s)",
                [new_id, it["dish_id"], it["dish_name"], it["price"], it["quantity"]],
            )
        cur.execute(
            "UPDATE restaurants SET sales = sales + %s WHERE id = %s",
            [sum(it["quantity"] for it in cleaned_items), int(restaurant_id)],
        )

    order_row = myapp_db.queryone(
        "SELECT id, restaurant_id, restaurant_name, customer_name, phone, address, note, "
        "total_amount, status, created_at FROM orders WHERE id = %s",
        [new_id],
    )
    item_rows = myapp_db.query(
        "SELECT id, order_id, dish_id, dish_name, price, quantity FROM order_items "
        "WHERE order_id = %s ORDER BY id ASC",
        [new_id],
    )
    return jsonify(
        ok=True,
        order=_row_to_order(order_row, [_row_to_order_item(it) for it in item_rows]),
    ), 201


# ============ 健康检查 / 统计 ============

@app.get("/stats")
def stats():
    row = myapp_db.queryone(
        "SELECT COUNT(*)::int AS total_restaurants FROM restaurants"
    )
    dish_row = myapp_db.queryone(
        "SELECT COUNT(*)::int AS total_dishes FROM dishes"
    )
    order_row = myapp_db.queryone(
        "SELECT COUNT(*)::int AS total_orders, COALESCE(SUM(total_amount), 0)::float AS total_amount "
        "FROM orders"
    )
    return jsonify(
        ok=True,
        total_restaurants=row["total_restaurants"] if row else 0,
        total_dishes=dish_row["total_dishes"] if dish_row else 0,
        total_orders=order_row["total_orders"] if order_row else 0,
        total_gmv=float(order_row["total_amount"]) if order_row else 0.0,
        time=_now_iso(),
    )


@app.get("/ping")
def ping():
    return jsonify(ok=True, message="pong", time=_now_iso())