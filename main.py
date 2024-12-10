from flask import Flask, request, jsonify
from models import db, User, Seller, Food, Order, OrderDetail
from auth import register_user, register_seller, login_user, login_seller,token_required_seller,token_required_user
from flask_cors import CORS

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads/'  # مسیر ذخیره تصاویر
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)



# ثبت و ورود
@app.route("/user/register", methods=["POST"])
def user_register():
    return register_user()

@app.route("/user/login", methods=["POST"])
def user_login():
    return login_user()

@app.route("/seller/register", methods=["POST"])
def seller_register():
    return register_seller()

@app.route("/seller/login", methods=["POST"])
def seller_login():
    return login_seller()

# بررسی نوع فایل مجاز
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#اپلود تصویر فروشنده
@app.route('/seller/upload_image', methods=['POST'])
@token_required_seller
def upload_image():
    if 'image' not in request.files:
        return jsonify({"message": "تصویری ارسال نشده است."}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "نام فایل خالی است."}), 400

    if not allowed_file(file.filename):
        return jsonify({"message": "فرمت فایل مجاز نیست. فقط png، jpg و jpeg پشتیبانی می‌شوند."}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    # به‌روزرسانی تصویر فروشنده
    request.seller.image = file_path
    db.session.commit()

    return jsonify({"message": "تصویر با موفقیت آپلود شد.", "image_url": file_path}), 200

# CRUD غذاها
@app.route("/foods", methods=["POST"])
@token_required_seller
def add_food():
    data = request.json
    food = Food(
        seller_id=request.seller.id,
        name=data["name"],
        description=data["description"],
        price=data["price"],
        availability=data.get("availability", True)
    )
    db.session.add(food)
    db.session.commit()
    return jsonify({"message": "غذا اضافه شد."}), 201

@app.route("/foods", methods=["GET"])
@token_required_seller
def get_foods():
    foods = Food.query.all()
    return jsonify([{
        "id": food.id,
        "name": food.name,
        "description": food.description,
        "price": food.price,
        "availability": food.availability,
        "seller_id": food.seller_id
    } for food in foods]), 200

@app.route("/foods/<int:food_id>", methods=["PUT"])
@token_required_seller
def update_food(food_id):
    food = Food.query.get_or_404(food_id)
    if food.seller_id != request.seller.id:
        return jsonify({"message": "شما مجاز به ویرایش این غذا نیستید."}), 403
    data = request.json
    food.name = data.get("name", food.name)
    food.description = data.get("description", food.description)
    food.price = data.get("price", food.price)
    food.availability = data.get("availability", food.availability)
    db.session.commit()
    return jsonify({"message": "غذا ویرایش شد."}), 200

@app.route("/foods/<int:food_id>", methods=["DELETE"])
@token_required_seller
def delete_food(food_id):
    food = Food.query.get_or_404(food_id)
    if food.seller_id != request.seller.id:
        return jsonify({"message": "شما مجاز به حذف این غذا نیستید."}), 403
    db.session.delete(food)
    db.session.commit()
    return jsonify({"message": "غذا حذف شد."}), 200

# CRUD سفارشات
@app.route("/orders", methods=["POST"])
@token_required_user
def place_order():
    """افزودن سفارش جدید"""
    data = request.json
    if not data.get("seller_id") or not data.get("details") or not isinstance(data["details"], list):
        return jsonify({"message": "اطلاعات سفارش ناقص است."}), 400

    total_price = 0
    for item in data["details"]:
        food = Food.query.get(item["food_id"])
        if not food or not food.availability:
            return jsonify({"message": f"غذا با آی‌دی {item['food_id']} موجود نیست."}), 400
        total_price += food.price * item["quantity"]

    new_order = Order(
        user_id=request.seller.id,  # از توکن کاربر
        seller_id=data["seller_id"],
        total_price=total_price,
        status="در حال پردازش"
    )
    db.session.add(new_order)
    db.session.commit()

    for item in data["details"]:
        order_detail = OrderDetail(
            order_id=new_order.id,
            food_id=item["food_id"],
            quantity=item["quantity"],
            price=Food.query.get(item["food_id"]).price
        )
        db.session.add(order_detail)
    db.session.commit()

    return jsonify({"message": "سفارش با موفقیت ثبت شد.", "order_id": new_order.id}), 201


@app.route("/orders", methods=["GET"])
@token_required_user
def get_user_orders():
    """دریافت لیست سفارش‌های کاربر"""
    orders = Order.query.filter_by(user_id=request.seller.id).all()
    return jsonify([{
        "id": order.id,
        "order_date": order.order_date,
        "total_price": order.total_price,
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "quantity": detail.quantity,
            "price": detail.price
        } for detail in order.details]
    } for order in orders]), 200


@app.route("/orders/<int:order_id>", methods=["PUT"])
@token_required_user
def update_order(order_id):
    """ویرایش وضعیت سفارش"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != request.seller.id:
        return jsonify({"message": "شما مجاز به ویرایش این سفارش نیستید."}), 403

    data = request.json
    order.status = data.get("status", order.status)
    db.session.commit()
    return jsonify({"message": "وضعیت سفارش با موفقیت ویرایش شد."}), 200


@app.route("/orders/<int:order_id>", methods=["DELETE"])
@token_required_user
def delete_order(order_id):
    """حذف سفارش"""
    order = Order.query.get_or_404(order_id)
    if order.user_id != request.seller.id:
        return jsonify({"message": "شما مجاز به حذف این سفارش نیستید."}), 403

    # حذف جزئیات سفارش
    OrderDetail.query.filter_by(order_id=order.id).delete()
    # حذف سفارش
    db.session.delete(order)
    db.session.commit()
    return jsonify({"message": "سفارش با موفقیت حذف شد."}), 200


# راه‌اندازی سرور
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ایجاد جداول در پایگاه‌داده
    app.run(debug=True)
