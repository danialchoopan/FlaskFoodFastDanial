from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, Seller, Food, Order, OrderDetail, Comment
from utils.decorators import seller_login_required
from utils.order_status import OrderStatus
from werkzeug.utils import secure_filename
from flask import current_app
import os
import json
from datetime import datetime, timedelta

web_seller_bp = Blueprint('web_seller', __name__)


def seller_login_required_web(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("seller_id"):
            return redirect(url_for("web_seller.login"))
        return f(*args, **kwargs)
    return decorated


@web_seller_bp.route("/seller/web/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")
        seller = Seller.query.filter_by(phone=phone).first()
        if seller and seller.check_password(password):
            if not seller.is_active:
                flash("حساب شما مسدود شده است.", "error")
                return redirect(url_for("web_seller.login"))
            session["seller_id"] = seller.id
            session["seller_restaurant_name"] = seller.restaurant_name
            return redirect(url_for("web_seller.dashboard"))
        flash("شماره تلفن یا رمز عبور اشتباه است.", "error")
    return render_template("seller/login.html")


@web_seller_bp.route("/seller/web/logout")
def logout():
    session.pop("seller_id", None)
    session.pop("seller_restaurant_name", None)
    return redirect(url_for("web_seller.login"))


@web_seller_bp.route("/seller/web/dashboard")
@seller_login_required_web
def dashboard():
    seller_id = session["seller_id"]
    seller = Seller.query.get_or_404(seller_id)

    today = datetime.utcnow().date()
    today_orders = Order.query.filter(
        Order.seller_id == seller_id,
        Order.order_date >= datetime.combine(today, datetime.min.time())
    ).all()

    total_orders = Order.query.filter_by(seller_id=seller_id).count()
    completed_orders = Order.query.filter_by(seller_id=seller_id, status=OrderStatus.COMPLETED).all()
    total_revenue = sum(float(o.total_price) for o in completed_orders)

    recent_orders = Order.query.filter_by(seller_id=seller_id).order_by(Order.order_date.desc()).limit(5).all()

    return render_template("seller/dashboard.html",
                           seller=seller,
                           today_orders_count=len(today_orders),
                           today_revenue=sum(float(o.total_price) for o in today_orders if o.status == OrderStatus.COMPLETED),
                           total_orders=total_orders,
                           total_revenue=total_revenue,
                           avg_rating=seller.average_rating,
                           recent_orders=recent_orders)


@web_seller_bp.route("/seller/web/orders")
@seller_login_required_web
def orders():
    seller_id = session["seller_id"]
    tab = request.args.get('tab', 'active')

    query = Order.query.filter_by(seller_id=seller_id)
    if tab == 'active':
        query = query.filter(Order.status.in_(OrderStatus.active_statuses()))
    elif tab == 'completed':
        query = query.filter_by(status=OrderStatus.COMPLETED)
    elif tab == 'cancelled':
        query = query.filter(Order.status.in_([OrderStatus.CANCELLED_BY_SELLER, OrderStatus.CANCELLED_BY_USER]))

    orders_list = query.order_by(Order.order_date.desc()).all()
    return render_template("seller/orders.html", orders=orders_list, tab=tab)


@web_seller_bp.route("/seller/web/orders/<int:order_id>/status", methods=["POST"])
@seller_login_required_web
def update_order_status(order_id):
    seller_id = session["seller_id"]
    order = Order.query.filter_by(id=order_id, seller_id=seller_id).first()
    if not order:
        flash("سفارش یافت نشد.", "error")
        return redirect(url_for("web_seller.orders"))

    action = request.form.get("action")
    if action == "confirm":
        order.status = OrderStatus.CONFIRMED
    elif action == "preparing":
        order.status = OrderStatus.PREPARING
    elif action == "complete":
        order.status = OrderStatus.COMPLETED
    elif action == "cancel":
        order.status = OrderStatus.CANCELLED_BY_SELLER

    db.session.commit()
    flash("وضعیت سفارش بروزرسانی شد.", "success")
    return redirect(url_for("web_seller.orders"))


@web_seller_bp.route("/seller/web/menu")
@seller_login_required_web
def menu():
    seller_id = session["seller_id"]
    foods = Food.query.filter_by(seller_id=seller_id).all()
    return render_template("seller/menu.html", foods=foods)


@web_seller_bp.route("/seller/web/menu/add", methods=["POST"])
@seller_login_required_web
def add_food():
    seller_id = session["seller_id"]
    name = request.form.get("name")
    price = request.form.get("price")
    description = request.form.get("description", "")

    if not name or not price:
        flash("نام و قیمت غذا الزامی است.", "error")
        return redirect(url_for("web_seller.menu"))

    photo = request.files.get("photo")
    photo_path = None
    if photo and photo.filename:
        filename = secure_filename(f"{seller_id}_{photo.filename}")
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        photo.save(filepath)
        photo_path = filepath

    new_food = Food(
        seller_id=seller_id,
        name=name,
        price=float(price),
        description=description,
        photo=photo_path,
        availability=True
    )
    db.session.add(new_food)
    db.session.commit()
    flash("غذا با موفقیت اضافه شد.", "success")
    return redirect(url_for("web_seller.menu"))


@web_seller_bp.route("/seller/web/menu/edit/<int:food_id>", methods=["POST"])
@seller_login_required_web
def edit_food(food_id):
    seller_id = session["seller_id"]
    food = Food.query.filter_by(id=food_id, seller_id=seller_id).first()
    if not food:
        flash("غذا یافت نشد.", "error")
        return redirect(url_for("web_seller.menu"))

    food.name = request.form.get("name", food.name)
    food.price = float(request.form.get("price", food.price))
    food.description = request.form.get("description", food.description)

    photo = request.files.get("photo")
    if photo and photo.filename:
        filename = secure_filename(f"{seller_id}_{photo.filename}")
        upload_dir = current_app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        filepath = os.path.join(upload_dir, filename)
        photo.save(filepath)
        food.photo = filepath

    db.session.commit()
    flash("غذا بروزرسانی شد.", "success")
    return redirect(url_for("web_seller.menu"))


@web_seller_bp.route("/seller/web/menu/delete/<int:food_id>", methods=["POST"])
@seller_login_required_web
def delete_food(food_id):
    seller_id = session["seller_id"]
    food = Food.query.filter_by(id=food_id, seller_id=seller_id).first()
    if not food:
        flash("غذا یافت نشد.", "error")
        return redirect(url_for("web_seller.menu"))

    db.session.delete(food)
    db.session.commit()
    flash("غذا حذف شد.", "success")
    return redirect(url_for("web_seller.menu"))


@web_seller_bp.route("/seller/web/menu/toggle/<int:food_id>", methods=["POST"])
@seller_login_required_web
def toggle_food(food_id):
    seller_id = session["seller_id"]
    food = Food.query.filter_by(id=food_id, seller_id=seller_id).first()
    if food:
        food.availability = not food.availability
        db.session.commit()
    return redirect(url_for("web_seller.menu"))


@web_seller_bp.route("/seller/web/reports")
@seller_login_required_web
def reports():
    seller_id = session["seller_id"]
    period = request.args.get('period', 'weekly')

    now = datetime.utcnow()
    if period == 'daily':
        start = now - timedelta(days=7)
    elif period == 'monthly':
        start = now - timedelta(days=30)
    else:
        start = now - timedelta(weeks=4)

    completed = Order.query.filter(
        Order.seller_id == seller_id,
        Order.status == OrderStatus.COMPLETED,
        Order.order_date >= start
    ).all()

    total_revenue = sum(float(o.total_price) for o in completed)
    total_orders = len(completed)

    # Top items
    food_sales = {}
    for order in completed:
        for detail in order.details:
            fid = detail.food_id
            if fid not in food_sales:
                food = Food.query.get(fid)
                food_sales[fid] = {'name': food.name if food else 'نامشخص', 'count': 0, 'revenue': 0}
            food_sales[fid]['count'] += detail.quantity
            food_sales[fid]['revenue'] += float(detail.price) * detail.quantity

    top_items = sorted(food_sales.values(), key=lambda x: x['revenue'], reverse=True)[:10]

    return render_template("seller/reports.html",
                           period=period,
                           total_revenue=total_revenue,
                           total_orders=total_orders,
                           top_items=top_items)


@web_seller_bp.route("/seller/web/profile", methods=["GET", "POST"])
@seller_login_required_web
def profile():
    seller_id = session["seller_id"]
    seller = Seller.query.get_or_404(seller_id)

    if request.method == "POST":
        seller.restaurant_name = request.form.get("restaurant_name", seller.restaurant_name)
        seller.address = request.form.get("address", seller.address)
        seller.city_name = request.form.get("city_name", seller.city_name)
        seller.category = request.form.get("category", seller.category)

        if request.form.get("latitude"):
            seller.latitude = float(request.form["latitude"])
        if request.form.get("longitude"):
            seller.longitude = float(request.form["longitude"])

        banner = request.files.get("banner")
        if banner and banner.filename:
            filename = secure_filename(f"banner_{seller_id}_{banner.filename}")
            upload_dir = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            banner.save(filepath)
            seller.image = filepath

        if request.form.get("open") == "on":
            seller.open = True
        else:
            seller.open = False

        db.session.commit()
        session["seller_restaurant_name"] = seller.restaurant_name
        flash("پروفایل بروزرسانی شد.", "success")
        return redirect(url_for("web_seller.profile"))

    return render_template("seller/profile.html", seller=seller)


@web_seller_bp.route("/seller/web/reviews")
@seller_login_required_web
def reviews():
    seller_id = session["seller_id"]
    comments = Comment.query.filter_by(seller_id=seller_id).order_by(Comment.created_at.desc()).all()
    seller = Seller.query.get_or_404(seller_id)
    return render_template("seller/reviews.html", comments=comments, avg_rating=seller.average_rating, total_ratings=seller.total_ratings)
