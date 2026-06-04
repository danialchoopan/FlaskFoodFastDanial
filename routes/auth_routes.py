from flask import Blueprint, request, jsonify
from models import db, User, Seller
import secrets
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/user/register", methods=["POST"])
def register_user():
    data = request.json
    if not data.get("name") or not data.get("phone") or not data.get("password"):
        return jsonify({"message": "تمام اطلاعات الزامی است."}), 400

    if User.query.filter_by(phone=data["phone"]).first():
        return jsonify({"message": "شماره تلفن قبلا ثبت شده است."}), 400

    new_user = User(
        name=data["name"],
        city_name=data.get("city_name"),
        address=data.get("address"),
        phone=data["phone"],
        latitude=data.get("latitude"),
        longitude=data.get("longitude")
    )
    new_user.set_password(data["password"])
    new_user.token = secrets.token_hex(16)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "ثبت‌نام کاربر با موفقیت انجام شد.",
        "token": new_user.token,
        "name": new_user.name,
        "phone": new_user.phone,
        "city_name": new_user.city_name,
        "id": new_user.id,
    }), 201

@auth_bp.route("/seller/register", methods=["POST"])
def register_seller():
    data = request.json
    if not data.get("phone") or not data.get("password") or not data.get("restaurant_name"):
         return jsonify({"message": "تمام اطلاعات الزامی است."}), 400

    if Seller.query.filter_by(phone=data["phone"]).first():
        return jsonify({"message": "شماره تلفن قبلا ثبت شده است."}), 400

    new_seller = Seller(
        restaurant_name=data["restaurant_name"],
        city_name=data.get("city_name"),
        category=data.get("category"),
        phone=data["phone"],
        address=data.get("address"),
        latitude=data.get("latitude"),
        longitude=data.get("longitude")
    )
    new_seller.set_password(data["password"])
    new_seller.token = secrets.token_hex(16)

    db.session.add(new_seller)
    db.session.commit()

    return jsonify({
        "message": "ثبت‌نام فروشنده با موفقیت انجام شد.",
        "token": new_seller.token,
        "name": new_seller.restaurant_name,
        "phone": new_seller.phone,
        "city_name": new_seller.city_name,
        "id": new_seller.id,
    }), 201

@auth_bp.route("/user/login", methods=["POST"])
def login_user():
    data = request.json
    if not data.get("phone") or not data.get("password"):
        return jsonify({"message": "شماره تلفن و رمز عبور الزامی هستند."}), 400

    user = User.query.filter_by(phone=data["phone"]).first()
    if not user or not user.check_password(data["password"]):
        return jsonify({"message": "شماره تلفن یا رمز عبور اشتباه است."}), 401

    if not user.is_active:
        return jsonify({"message": "حساب کاربری شما مسدود شده است."}), 403

    user.token = secrets.token_hex(16)
    db.session.commit()

    return jsonify({
        "message": "کاربر با موفقیت وارد شد",
        "token": user.token,
        "name": user.name,
        "phone": user.phone,
        "city_name": user.city_name,
        "id": user.id,
    }), 200

@auth_bp.route("/seller/login", methods=["POST"])
def login_seller():
    data = request.json
    if not data.get("phone") or not data.get("password"):
        return jsonify({"message": "شماره تلفن و رمز عبور الزامی هستند."}), 400

    seller = Seller.query.filter_by(phone=data["phone"]).first()
    if not seller or not seller.check_password(data["password"]):
        return jsonify({"message": "شماره تلفن یا رمز عبور اشتباه است."}), 401

    if not seller.is_active:
        return jsonify({"message": "حساب فروشندگی شما مسدود شده است."}), 403

    seller.token = secrets.token_hex(16)
    db.session.commit()

    return jsonify({
        "message": "فروشنده با موفقیت وارد شد",
        "token": seller.token,
        "restaurant_name": seller.restaurant_name,
        "phone": seller.phone,
        "city_name": seller.city_name,
        "id": seller.id,
    }), 200

def token_required_seller(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "توکن الزامی است."}), 401
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        seller = Seller.query.filter_by(token=token).first()
        if not seller or not seller.is_active:
            return jsonify({"message": "توکن معتبر نیست یا حساب مسدود است."}), 401
        request.seller = seller
        return f(*args, **kwargs)
    return decorated

def token_required_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "توکن الزامی است."}), 401
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        user = User.query.filter_by(token=token).first()
        if not user or not user.is_active:
            return jsonify({"message": "توکن معتبر نیست یا حساب مسدود است."}), 401
        request.user = user
        return f(*args, **kwargs)
    return decorated
