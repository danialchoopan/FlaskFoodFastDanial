from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models import db, User, Seller, Food, Order, OrderDetail, Comment
from utils.order_status import OrderStatus
import secrets

web_user_bp = Blueprint('web_user', __name__)

@web_user_bp.route("/")
def index():
    city = request.args.get('city')
    if city:
        restaurants = Seller.query.filter_by(city_name=city, is_active=True).all()
    else:
        restaurants = Seller.query.filter_by(is_active=True).all()
    return render_template("user/index.html", restaurants=restaurants)

@web_user_bp.route("/restaurant/<int:id>")
def restaurant_detail(id):
    restaurant = Seller.query.get_or_404(id)
    return render_template("user/restaurant.html", restaurant=restaurant)

@web_user_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")
        user = User.query.filter_by(phone=phone).first()
        if user and user.check_password(password):
            if not user.is_active:
                flash("حساب شما مسدود شده است.", "error")
                return redirect(url_for("web_user.login"))
            session["user_id"] = user.id
            session["user_name"] = user.name
            return redirect(url_for("web_user.index"))
        flash("شماره تلفن یا رمز عبور اشتباه است.", "error")
    return render_template("user/login.html")

@web_user_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("cart", None)
    return redirect(url_for("web_user.index"))

@web_user_bp.route("/add_to_cart", methods=["POST"])
def add_to_cart():
    food_id = request.form.get("food_id")
    food = Food.query.get_or_404(food_id)
    cart = session.get("cart", [])

    found = False
    for item in cart:
        if item['id'] == food.id:
            item['quantity'] += 1
            found = True
            break
    if not found:
        cart.append({
            'id': food.id,
            'name': food.name,
            'price': float(food.price),
            'quantity': 1
        })

    session["cart"] = cart
    session["total_price"] = sum(item['price'] * item['quantity'] for item in cart)
    flash(f"{food.name} به سبد خرید اضافه شد.", "success")
    return redirect(url_for("web_user.restaurant_detail", id=food.seller_id))

@web_user_bp.route("/place_order", methods=["POST"])
def place_order():
    if not session.get("user_id"):
        flash("لطفا ابتدا وارد حساب خود شوید.", "error")
        return redirect(url_for("web_user.login"))

    seller_id = request.form.get("seller_id")
    cart = session.get("cart")
    if not cart:
        flash("سبد خرید شما خالی است.", "error")
        return redirect(url_for("web_user.index"))

    new_order = Order(
        user_id=session["user_id"],
        seller_id=seller_id,
        total_price=session["total_price"],
        status=OrderStatus.WAITING_CONFIRMATION
    )
    db.session.add(new_order)
    db.session.flush()

    for item in cart:
        detail = OrderDetail(
            order_id=new_order.id,
            food_id=item['id'],
            quantity=item['quantity'],
            price=item['price']
        )
        db.session.add(detail)

    db.session.commit()
    session.pop("cart", None)
    session.pop("total_price", None)
    flash("سفارش شما با موفقیت ثبت شد.", "success")
    return redirect(url_for("web_user.get_orders"))

@web_user_bp.route("/orders")
def get_orders():
    if not session.get("user_id"):
        return redirect(url_for("web_user.login"))
    orders = Order.query.filter_by(user_id=session["user_id"]).order_by(Order.order_date.desc()).all()
    return render_template("user/orders.html", orders=orders)

@web_user_bp.route("/add_comment", methods=["POST"])
def add_comment():
    if not session.get("user_id"):
        flash("برای ثبت نظر باید وارد شوید.", "error")
        return redirect(url_for("web_user.login"))

    seller_id = request.form.get("seller_id")
    content = request.form.get("content")
    rating = request.form.get("rating", type=int)

    new_comment = Comment(
        user_id=session["user_id"],
        seller_id=seller_id,
        content=content,
        rating=rating
    )
    db.session.add(new_comment)
    db.session.commit()
    flash("نظر شما با موفقیت ثبت شد.", "success")
    return redirect(url_for("web_user.restaurant_detail", id=seller_id))
