from flask import Blueprint, request, jsonify, session
from models import db, User, Seller, Food, Order, OrderDetail, Comment, Setting
from utils.order_status import OrderStatus
from utils.pagination import paginate_query
from sqlalchemy import func
from datetime import datetime, timedelta
import json

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin/api')


def admin_api_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ── Users ────────────────────────────────────────────────────────────

@admin_api_bp.route("/users")
@admin_api_required
def list_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = User.query
    if search:
        query = query.filter(db.or_(User.name.contains(search), User.phone.contains(search)))
    result = paginate_query(query.order_by(User.created_at.desc()), page)
    return jsonify({
        "items": [{"id": u.id, "name": u.name, "phone": u.phone, "city": u.city_name,
                   "is_active": u.is_active, "created_at": str(u.created_at)} for u in result["items"]],
        "total": result["total"], "page": result["page"], "pages": result["pages"]
    })


@admin_api_bp.route("/users/<int:user_id>")
@admin_api_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.order_date.desc()).limit(10).all()
    return jsonify({
        "id": user.id, "name": user.name, "phone": user.phone, "city": user.city_name,
        "address": user.address, "is_active": user.is_active, "created_at": str(user.created_at),
        "orders": [{"id": o.id, "total": float(o.total_price), "status": o.status,
                    "date": str(o.order_date)} for o in orders]
    })


@admin_api_bp.route("/users/<int:user_id>/toggle", methods=["PUT"])
@admin_api_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    return jsonify({"success": True, "is_active": user.is_active})


# ── Sellers ──────────────────────────────────────────────────────────

@admin_api_bp.route("/sellers")
@admin_api_required
def list_sellers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Seller.query
    if search:
        query = query.filter(db.or_(Seller.restaurant_name.contains(search), Seller.phone.contains(search)))
    result = paginate_query(query.order_by(Seller.created_at.desc()), page)
    return jsonify({
        "items": [{"id": s.id, "name": s.restaurant_name, "phone": s.phone, "city": s.city_name,
                   "category": s.category, "is_active": s.is_active, "rating": s.average_rating,
                   "created_at": str(s.created_at)} for s in result["items"]],
        "total": result["total"], "page": result["page"], "pages": result["pages"]
    })


@admin_api_bp.route("/sellers/<int:seller_id>")
@admin_api_required
def get_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    order_count = Order.query.filter_by(seller_id=seller_id).count()
    total_sales = db.session.query(func.sum(Order.total_price)).filter_by(seller_id=seller_id).scalar() or 0
    return jsonify({
        "id": seller.id, "name": seller.restaurant_name, "phone": seller.phone,
        "city": seller.city_name, "category": seller.category, "address": seller.address,
        "is_active": seller.is_active, "rating": seller.average_rating,
        "order_count": order_count, "total_sales": float(total_sales)
    })


@admin_api_bp.route("/sellers/<int:seller_id>/toggle", methods=["PUT"])
@admin_api_required
def toggle_seller(seller_id):
    seller = Seller.query.get_or_404(seller_id)
    seller.is_active = not seller.is_active
    db.session.commit()
    return jsonify({"success": True, "is_active": seller.is_active})


# ── Orders ───────────────────────────────────────────────────────────

@admin_api_bp.route("/orders")
@admin_api_required
def list_orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    seller_filter = request.args.get('seller', '', type=str)
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if seller_filter:
        query = query.join(Seller).filter(Seller.restaurant_name.contains(seller_filter))
    result = paginate_query(query.order_by(Order.order_date.desc()), page)
    return jsonify({
        "items": [{"id": o.id, "user_name": o.user.name, "seller_name": o.seller.restaurant_name,
                   "total": float(o.total_price), "status": o.status,
                   "date": str(o.order_date)} for o in result["items"]],
        "total": result["total"], "page": result["page"], "pages": result["pages"]
    })


@admin_api_bp.route("/orders/<int:order_id>")
@admin_api_required
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    details = OrderDetail.query.filter_by(order_id=order_id).all()
    return jsonify({
        "id": order.id, "user_name": order.user.name, "seller_name": order.seller.restaurant_name,
        "total": float(order.total_price), "status": order.status, "date": str(order.order_date),
        "items": [{"food_name": d.food.name, "quantity": d.quantity, "price": float(d.price)} for d in details]
    })


# ── Analytics ────────────────────────────────────────────────────────

@admin_api_bp.route("/analytics/overview")
@admin_api_required
def analytics_overview():
    return jsonify({
        "users_count": User.query.count(),
        "sellers_count": Seller.query.count(),
        "orders_count": Order.query.count(),
        "total_sales": float(db.session.query(func.sum(Order.total_price)).scalar() or 0)
    })


@admin_api_bp.route("/analytics/revenue")
@admin_api_required
def analytics_revenue():
    now = datetime.utcnow()
    months = []
    for i in range(5, -1, -1):
        d = now - timedelta(days=30 * i)
        start = d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if d.month == 12:
            end = start.replace(year=start.year + 1, month=1)
        else:
            end = start.replace(month=start.month + 1)
        revenue = db.session.query(func.sum(Order.total_price)).filter(
            Order.order_date >= start, Order.order_date < end
        ).scalar() or 0
        months.append({"month": start.strftime("%Y-%m"), "revenue": float(revenue)})
    return jsonify(months)


@admin_api_bp.route("/analytics/order-status")
@admin_api_required
def analytics_order_status():
    statuses = {}
    for s in OrderStatus.all():
        statuses[s] = Order.query.filter_by(status=s).count()
    return jsonify(statuses)


@admin_api_bp.route("/analytics/daily-orders")
@admin_api_required
def analytics_daily_orders():
    now = datetime.utcnow()
    days = []
    for i in range(6, -1, -1):
        d = now - timedelta(days=i)
        start = d.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        count = Order.query.filter(Order.order_date >= start, Order.order_date < end).count()
        days.append({"date": start.strftime("%m/%d"), "count": count})
    return jsonify(days)


@admin_api_bp.route("/analytics/top-restaurants")
@admin_api_required
def analytics_top_restaurants():
    results = db.session.query(
        Seller.restaurant_name,
        func.sum(Order.total_price).label('total_sales'),
        func.count(Order.id).label('order_count')
    ).join(Order, Seller.id == Order.seller_id
    ).group_by(Seller.id
    ).order_by(func.sum(Order.total_price).desc()
    ).limit(5).all()
    return jsonify([{"name": r[0], "sales": float(r[1]), "orders": r[2]} for r in results])


# ── Comments ─────────────────────────────────────────────────────────

@admin_api_bp.route("/comments")
@admin_api_required
def list_comments():
    page = request.args.get('page', 1, type=int)
    rating_filter = request.args.get('rating', '', type=str)
    query = Comment.query
    if rating_filter:
        query = query.filter_by(rating=int(rating_filter))
    result = paginate_query(query.order_by(Comment.created_at.desc()), page)
    return jsonify({
        "items": [{"id": c.id, "user_name": c.user.name, "seller_name": c.seller.restaurant_name,
                   "content": c.content, "rating": c.rating,
                   "created_at": str(c.created_at)} for c in result["items"]],
        "total": result["total"], "page": result["page"], "pages": result["pages"]
    })


@admin_api_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@admin_api_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    return jsonify({"success": True})


# ── Settings ─────────────────────────────────────────────────────────

@admin_api_bp.route("/settings")
@admin_api_required
def get_settings():
    settings = {}
    for s in Setting.query.all():
        try:
            settings[s.key] = json.loads(s.value)
        except (json.JSONDecodeError, TypeError):
            settings[s.key] = s.value
    return jsonify(settings)


@admin_api_bp.route("/settings", methods=["PUT"])
@admin_api_required
def update_settings():
    data = request.json
    for key, value in data.items():
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = json.dumps(value) if isinstance(value, (list, dict)) else str(value)
        else:
            db.session.add(Setting(key=key, value=json.dumps(value) if isinstance(value, (list, dict)) else str(value)))
    db.session.commit()
    return jsonify({"success": True})


@admin_api_bp.route("/settings/categories", methods=["GET"])
@admin_api_required
def get_categories():
    setting = Setting.query.filter_by(key='food_categories').first()
    categories = json.loads(setting.value) if setting else []
    return jsonify(categories)


@admin_api_bp.route("/settings/categories", methods=["POST"])
@admin_api_required
def add_category():
    data = request.json
    category = data.get('name', '')
    setting = Setting.query.filter_by(key='food_categories').first()
    categories = json.loads(setting.value) if setting else []
    categories.append(category)
    if setting:
        setting.value = json.dumps(categories)
    else:
        db.session.add(Setting(key='food_categories', value=json.dumps(categories)))
    db.session.commit()
    return jsonify({"success": True})


@admin_api_bp.route("/settings/categories/<int:index>", methods=["DELETE"])
@admin_api_required
def delete_category(index):
    setting = Setting.query.filter_by(key='food_categories').first()
    if setting:
        categories = json.loads(setting.value)
        if 0 <= index < len(categories):
            categories.pop(index)
            setting.value = json.dumps(categories)
            db.session.commit()
    return jsonify({"success": True})


@admin_api_bp.route("/settings/cities", methods=["GET"])
@admin_api_required
def get_cities():
    setting = Setting.query.filter_by(key='cities').first()
    cities = json.loads(setting.value) if setting else []
    return jsonify(cities)


@admin_api_bp.route("/settings/cities", methods=["POST"])
@admin_api_required
def add_city():
    data = request.json
    city = data.get('name', '')
    setting = Setting.query.filter_by(key='cities').first()
    cities = json.loads(setting.value) if setting else []
    cities.append(city)
    if setting:
        setting.value = json.dumps(cities)
    else:
        db.session.add(Setting(key='cities', value=json.dumps(cities)))
    db.session.commit()
    return jsonify({"success": True})


@admin_api_bp.route("/settings/cities/<int:index>", methods=["DELETE"])
@admin_api_required
def delete_city(index):
    setting = Setting.query.filter_by(key='cities').first()
    if setting:
        cities = json.loads(setting.value)
        if 0 <= index < len(cities):
            cities.pop(index)
            setting.value = json.dumps(cities)
            db.session.commit()
    return jsonify({"success": True})
