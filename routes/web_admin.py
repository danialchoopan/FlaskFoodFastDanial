from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Seller, Food, Order, OrderDetail, Comment, Admin
import secrets

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
    return redirect(url_for("admin.login"))

@admin_bp.route("/admin/dashboard")
def dashboard():
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    stats = {
        "users_count": User.query.count(),
        "sellers_count": Seller.query.count(),
        "orders_count": Order.query.count(),
        "total_sales": db.session.query(db.func.sum(Order.total_price)).scalar() or 0
    }
    recent_orders = Order.query.order_by(Order.order_date.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_orders=recent_orders)

@admin_bp.route("/admin/management")
def management():
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    sellers = Seller.query.all()
    users = User.query.all()
    return render_template("admin/management.html", sellers=sellers, users=users)

@admin_bp.route("/admin/comments")
def comments():
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    all_comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template("admin/comments.html", comments=all_comments)

@admin_bp.route("/admin/toggle_user/<int:id>", methods=["POST"])
def toggle_user(id):
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"وضعیت کاربر {user.name} تغییر یافت.", "success")
    return redirect(url_for("admin.management"))

@admin_bp.route("/admin/toggle_seller/<int:id>", methods=["POST"])
def toggle_seller(id):
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    seller = Seller.query.get_or_404(id)
    seller.is_active = not seller.is_active
    db.session.commit()
    flash(f"وضعیت رستوران {seller.restaurant_name} تغییر یافت.", "success")
    return redirect(url_for("admin.management"))

@admin_bp.route("/admin/delete_comment/<int:id>", methods=["POST"])
def delete_comment(id):
    if not session.get("admin_id"): return redirect(url_for("admin.login"))
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash("نظر با موفقیت حذف شد.", "success")
    return redirect(url_for("admin.comments"))
