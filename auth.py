from flask import request, jsonify
from models import db, User, Seller
import secrets  # برای تولید توکن
from functools import wraps


# ثبت‌نام کاربر
def register_user():
    data = request.json
    if not data.get("name") or not data.get("phone") or not data.get("password"):
        return jsonify({"message": "تمام اطلاعات الزامی است."}), 400

    if User.query.filter_by(phone=data["phone"]).first():
        return jsonify({"message": "شماره تلفن قبلا ثبت شده است."}), 400

    new_user = User(
        name=data["name"],
        city_name=data["city_name"],
        address=data["address"],
        phone=data["phone"]
    )
    new_user.set_password(data["password"])  # تنظیم رمز عبور هش‌شده

    new_user.token = secrets.token_hex(16)  # تولید توکن یکتا

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "ثبت‌نام کاربر با موفقیت انجام شد.",
        "token":new_user.token
    }), 201

# ثبت‌نام فروشنده
def register_seller():
    data = request.json
    if not data.get("owner_name") or not data.get("phone") or not data.get("password") or not data["restaurant_name"] or not data["address_coordinate"]:
        return jsonify({"message": "تمام اطلاعات الزامی است."}), 400

    if Seller.query.filter_by(phone=data["phone"]).first():
        return jsonify({"message": "شماره تلفن قبلا ثبت شده است."}), 400

    new_seller = Seller(
        owner_name=data["owner_name"],
        restaurant_name=data["restaurant_name"],
        city_name=data["city_name"],
        category=data["category"],
        phone=data["phone"],
        address=data["address"],
        address_coordinate=data["address_coordinate"]
    )
    new_seller.set_password(data["password"])  # تنظیم رمز عبور هش‌شده

    new_seller.token = secrets.token_hex(16)  # تولید توکن یکتا

    db.session.add(new_seller)
    db.session.commit()

    return jsonify({
        "message": "ثبت‌نام فروشنده با موفقیت انجام شد.",
        "token": new_seller.token
    }), 201

# ورود کاربر
def login_user():
    data = request.json
    if not data.get("phone") or not data.get("password"):
        return jsonify({"message": "شماره تلفن و رمز عبور الزامی هستند."}), 400

    user = User.query.filter_by(phone=data["phone"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "شماره تلفن یا رمز عبور اشتباه است."}), 401

    user.token = secrets.token_hex(16)  # تولید توکن یکتا
    db.session.commit()

    return jsonify({
        "message":"کاربر با موفقیت وارد شد",
        "token": user.token}), 200

# ورود فروشنده
def login_seller():
    data = request.json
    if not data.get("phone") or not data.get("password"):
        return jsonify({"message": "شماره تلفن و رمز عبور الزامی هستند."}), 400

    seller = Seller.query.filter_by(phone=data["phone"]).first()
    if not seller or not seller.check_password(data["password"]):
        return jsonify({"message": "شماره تلفن یا رمز عبور اشتباه است."}), 401

    seller.token = secrets.token_hex(16)  # تولید توکن یکتا
    db.session.commit()

    return jsonify({
        "message":"فروشنده با موفقیت وارد شد",
        "token": seller.token}), 200

# میان‌افزار برای احراز هویت با توکن فروشنده
def token_required_seller(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "توکن الزامی است."}), 401

        # حذف پیشوند "Bearer " از توکن
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        seller = Seller.query.filter_by(token=token).first()
        if not seller:
            return jsonify({"message": "توکن معتبر نیست."}), 401

        request.seller = seller
        return f(*args, **kwargs)
    return decorated

#میان افزار کابر
def token_required_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "توکن الزامی است."}), 401

        # حذف پیشوند "Bearer " از توکن
        if token.startswith("Bearer "):
            token = token.split(" ")[1]

        print(token)
        seller = User.query.filter_by(token=token).first()
        if not seller:
            return jsonify({"message": "توکن معتبر نیست."}), 401

        request.seller = seller
        return f(*args, **kwargs)
    return decorated
