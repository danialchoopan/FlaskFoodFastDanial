from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models import db, User, Seller, Food, Order, OrderDetail, Comment, Admin, Setting
from utils.decorators import admin_login_required
from utils.order_status import OrderStatus
import json

admin_bp = Blueprint('admin', __name__)


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            return redirect(url_for("admin.dashboard"))
        flash("نام کاربری یا رمز عبور اشتباه است.", "error")
    return render_template("admin/login.html")


@admin_bp.route("/admin/logout")
def logout():
    session.pop("admin_id", None)
    session.pop("admin_username", None)
    return redirect(url_for("admin.login"))


@admin_bp.route("/admin/dashboard")
@admin_login_required
def dashboard():
    stats = {
        "users_count": User.query.count(),
        "sellers_count": Seller.query.count(),
        "orders_count": Order.query.count(),
        "total_sales": db.session.query(db.func.sum(Order.total_price)).scalar() or 0
    }
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)


@admin_bp.route("/admin/management")
@admin_login_required
def management():
    sellers = Seller.query.all()
    users = User.query.all()
    return render_template("admin/management.html", sellers=sellers, users=users)


@admin_bp.route("/admin/orders")
@admin_login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    seller_filter = request.args.get('seller', '', type=str)

    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if seller_filter:
        query = query.join(Seller).filter(Seller.restaurant_name.contains(seller_filter))

    pagination = query.order_by(Order.order_date.desc()).paginate(page=page, per_page=15, error_out=False)
    sellers = Seller.query.all()
    return render_template("admin/orders.html",
                           orders=pagination.items,
                           pagination=pagination,
                           sellers=sellers,
                           status_filter=status_filter,
                           seller_filter=seller_filter,
                           statuses=OrderStatus.all())


@admin_bp.route("/admin/sellers")
@admin_login_required
def sellers():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = Seller.query
    if search:
        query = query.filter(
            db.or_(Seller.restaurant_name.contains(search), Seller.phone.contains(search))
        )
    pagination = query.order_by(Seller.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/sellers.html", sellers=pagination.items, pagination=pagination, search=search)


@admin_bp.route("/admin/users")
@admin_login_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    query = User.query
    if search:
        query = query.filter(
            db.or_(User.name.contains(search), User.phone.contains(search))
        )
    pagination = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/users.html", users=pagination.items, pagination=pagination, search=search)


@admin_bp.route("/admin/comments")
@admin_login_required
def comments():
    page = request.args.get('page', 1, type=int)
    rating_filter = request.args.get('rating', '', type=str)
    query = Comment.query
    if rating_filter:
        query = query.filter_by(rating=int(rating_filter))
    pagination = query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template("admin/comments.html", comments=pagination.items, pagination=pagination, rating_filter=rating_filter)


@admin_bp.route("/admin/settings")
@admin_login_required
def settings():
    categories_setting = Setting.query.filter_by(key='food_categories').first()
    cities_setting = Setting.query.filter_by(key='cities').first()
    fee_setting = Setting.query.filter_by(key='platform_fee_percent').first()

    categories = json.loads(categories_setting.value) if categories_setting else []
    cities = json.loads(cities_setting.value) if cities_setting else []
    fee = fee_setting.value if fee_setting else "5"

    return render_template("admin/settings.html", categories=categories, cities=cities, fee=fee)


@admin_bp.route("/admin/toggle_user/<int:id>", methods=["POST"])
@admin_login_required
def toggle_user(id):
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"وضعیت کاربر {user.name} تغییر یافت.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/admin/toggle_seller/<int:id>", methods=["POST"])
@admin_login_required
def toggle_seller(id):
    seller = Seller.query.get_or_404(id)
    seller.is_active = not seller.is_active
    db.session.commit()
    flash(f"وضعیت رستوران {seller.restaurant_name} تغییر یافت.", "success")
    return redirect(url_for("admin.sellers"))


@admin_bp.route("/admin/delete_comment/<int:id>", methods=["POST"])
@admin_login_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash("نظر با موفقیت حذف شد.", "success")
    return redirect(url_for("admin.comments"))


@admin_bp.route("/admin/approve_seller/<int:id>", methods=["POST"])
@admin_login_required
def approve_seller(id):
    seller = Seller.query.get_or_404(id)
    seller.is_active = True
    db.session.commit()
    flash(f"رستوران {seller.restaurant_name} تایید شد.", "success")
    return redirect(url_for("admin.sellers"))


@admin_bp.route("/admin/settings/save", methods=["POST"])
@admin_login_required
def save_settings():
    categories = request.form.getlist('categories')
    cities = request.form.getlist('cities')
    fee = request.form.get('fee', '5')

    for key, value in [('food_categories', json.dumps(categories)), ('cities', json.dumps(cities)), ('platform_fee_percent', fee)]:
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            db.session.add(Setting(key=key, value=value))

    db.session.commit()
    flash("تنظیمات با موفقیت ذخیره شد.", "success")
    return redirect(url_for("admin.settings"))
