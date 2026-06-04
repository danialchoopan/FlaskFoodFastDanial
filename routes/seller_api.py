from flask import Blueprint, request, jsonify
from models import db, User, Seller, Food, Order, OrderDetail, Comment
from routes.auth_routes import token_required_seller
import os
from werkzeug.utils import secure_filename
from flask import current_app

seller_api_bp = Blueprint('seller_api', __name__)

@seller_api_bp.route("/seller/edit/password", methods=["POST"])
@token_required_seller
def edit_seller_password():
    data = request.json
    new_password = data.get("new_password")
    old_password = data.get("old_password")
    seller = Seller.query.get_or_404(request.seller.id)
    if not seller.check_password(old_password):
        return jsonify({"success": False, "message": "رمزعبور وارد شده شما اشتباه است"}), 400
    seller.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True}), 200

@seller_api_bp.route("/seller/edit/city", methods=["POST"])
@token_required_seller
def edit_seller_city():
    data = request.json
    new_city = data.get("new_city_name")
    if not new_city:
        return jsonify({"success": False}), 400
    seller = Seller.query.get_or_404(request.seller.id)
    seller.city_name = new_city
    if "latitude" in data: seller.latitude = data["latitude"]
    if "longitude" in data: seller.longitude = data["longitude"]
    db.session.commit()
    return jsonify({"success": True}), 200

@seller_api_bp.route("/seller/banner", methods=["GET"])
@token_required_seller
def get_restaurant_banner():
    seller = Seller.query.get_or_404(request.seller.id)
    return jsonify({"success": True, "img": seller.image.replace("\\", "/") if seller.image else ""}), 200

@seller_api_bp.route("/seller/banner/update", methods=["PUT"])
@token_required_seller
def edit_restaurant_banner():
    data = request.json
    seller = Seller.query.get_or_404(request.seller.id)
    photo_data = data.get("photo")
    if photo_data:
        try:
            from base64 import b64decode
            image_data = b64decode(photo_data.split(",")[-1])
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_filename = secure_filename(f"{seller.restaurant_name}_banner_{seller.id}.jpg")
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            seller.image = image_path
            db.session.commit()
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
    else:
        # Compatibility with simple string update if photo not in base64
        new_image = data.get("new_image")
        if new_image:
            seller.image = new_image
            db.session.commit()
        else:
            return jsonify({"success": False, "message": "No image data provided"}), 400

    return jsonify({"success": True, "img": seller.image.replace("\\", "/") if seller.image else ""}), 200

@seller_api_bp.route("/seller/open", methods=["POST"])
@token_required_seller
def seller_edit_open():
    data = request.json
    new_open = data.get("open")
    if new_open is None:
        return jsonify({"success": False}), 400
    seller = Seller.query.get_or_404(request.seller.id)
    seller.open = new_open
    db.session.commit()
    return jsonify({"success": True}), 200

@seller_api_bp.route("/seller/open/status", methods=["GET"])
@token_required_seller
def seller_open_status():
    seller = Seller.query.get_or_404(request.seller.id)
    return jsonify({"success": True, "seller_open": seller.open}), 200

@seller_api_bp.route("/seller/upload_image", methods=["POST"])
@token_required_seller
def upload_image():
    if 'image' not in request.files:
        return jsonify({"message": "فایلی ارسال نشده است"}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({"message": "فایلی انتخاب نشده است"}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({"message": "فایل با موفقیت آپلود شد", "filepath": filepath}), 200

@seller_api_bp.route("/seller/foods", methods=["POST"])
@token_required_seller
def add_food():
    data = request.json

    # Check for required fields
    if not all(key in data for key in ["name", "description", "price"]):
        return jsonify({"error": "Missing required fields"}), 400

    photo_data = data.get("photo")
    image_path = None
    if photo_data and photo_data.startswith("data:image"):
        try:
            from base64 import b64decode
            image_data = b64decode(photo_data.split(",")[-1])
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
            image_filename = secure_filename(f"{data['name']}_{request.seller.id}_image.jpg")
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
    else:
        image_path = photo_data # Use as string if not base64

    new_food = Food(
        seller_id=request.seller.id,
        name=data["name"],
        price=data["price"],
        description=data.get("description"),
        photo=image_path,
        availability=data.get("availability", True)
    )
    db.session.add(new_food)
    db.session.commit()
    return jsonify({"message": "غذا با موفقیت اضافه شد", "food_id": new_food.id}), 201

@seller_api_bp.route("/seller/food/<int:id>", methods=["GET"])
@token_required_seller
def get_food(id):
    food = Food.query.get_or_404(id)
    if food.seller_id != request.seller.id:
        return jsonify({"message": "دسترسی غیرمجاز"}), 403
    return jsonify({
        "id": food.id,
        "name": food.name,
        "price": food.price,
        "description": food.description,
        "photo": food.photo,
        "availability": food.availability
    }), 200

@seller_api_bp.route("/seller/foods", methods=["GET"])
@token_required_seller
def get_foods():
    foods = Food.query.filter_by(seller_id=request.seller.id).all()
    return jsonify([{
        "id": food.id,
        "name": food.name,
        "price": food.price,
        "description": food.description,
        "photo": food.photo,
        "availability": food.availability
    } for food in foods]), 200

@seller_api_bp.route("/seller/food/<int:food_id>", methods=["PUT"])
@token_required_seller
def update_food(food_id):
    food = Food.query.get_or_404(food_id)
    if food.seller_id != request.seller.id:
        return jsonify({"message": "دسترسی غیرمجاز"}), 403
    data = request.json
    food.name = data.get("name", food.name)
    food.price = data.get("price", food.price)
    food.description = data.get("description", food.description)
    food.photo = data.get("photo", food.photo)
    food.availability = data.get("availability", food.availability)
    db.session.commit()
    return jsonify({"message": "غذا با موفقیت بروزرسانی شد"}), 200

@seller_api_bp.route("/seller/foods/<int:food_id>", methods=["DELETE"])
@token_required_seller
def delete_food(food_id):
    food = Food.query.get_or_404(food_id)
    if food.seller_id != request.seller.id:
        return jsonify({"message": "دسترسی غیرمجاز"}), 403
    db.session.delete(food)
    db.session.commit()
    return jsonify({"message": "غذا با موفقیت حذف شد"}), 200

@seller_api_bp.route("/seller/orders/not", methods=["GET"])
@token_required_seller
def get_seller_orders_not_finish():
    orders = Order.query.filter(
        Order.seller_id == request.seller.id,
        Order.status != "سفارش شما تکمیل شد",
        Order.status != "لغو رستوران",
        Order.status != "لغو کاربر"
    ).all()
    return jsonify([{
        "id": order.id,
        "user_name": order.user.name,
        "total_price": float(order.total_price),
        "status": order.status,
        "order_date": order.order_date
    } for order in orders]), 200

@seller_api_bp.route("/seller/orders/all", methods=["GET"])
@token_required_seller
def get_seller_orders():
    orders = Order.query.filter_by(seller_id=request.seller.id).all()
    return jsonify([{
        "id": order.id,
        "user_name": order.user.name,
        "total_price": float(order.total_price),
        "status": order.status,
        "order_date": order.order_date
    } for order in orders]), 200

@seller_api_bp.route("/seller/orders/detail/<int:order_id>", methods=["GET"])
@token_required_seller
def get_seller_order_details(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=request.seller.id).first()
    if not order:
        return jsonify({"message": "سفارش یافت نشد"}), 404
    return jsonify({
        "id": order.id,
        "user_name": order.user.name,
        "user_phone": order.user.phone,
        "user_address": order.user.address,
        "total_price": float(order.total_price),
        "status": order.status,
        "details": [{
            "food_name": detail.food.name,
            "quantity": detail.quantity,
            "price": float(detail.price)
        } for detail in order.details]
    }), 200

@seller_api_bp.route("/seller/orders/preparing/<int:order_id>", methods=["PUT"])
@token_required_seller
def preparing_order(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=request.seller.id).first()
    if not order:
        return jsonify({"message": "سفارش یافت نشد"}), 404
    order.status = "در حال آماده‌سازی"
    db.session.commit()
    return jsonify({"message": "وضعیت سفارش تغییر یافت"}), 200

@seller_api_bp.route("/seller/orders/completed/<int:order_id>", methods=["PUT"])
@token_required_seller
def completed_order(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=request.seller.id).first()
    if not order:
        return jsonify({"message": "سفارش یافت نشد"}), 404
    order.status = "سفارش شما تکمیل شد"
    db.session.commit()
    return jsonify({"message": "سفارش تکمیل شد"}), 200

@seller_api_bp.route("/seller/orders/cancel/<int:order_id>", methods=["PUT"])
@token_required_seller
def seller_cancel_order(order_id):
    order = Order.query.filter_by(id=order_id, seller_id=request.seller.id).first()
    if not order:
        return jsonify({"message": "سفارش یافت نشد"}), 404
    order.status = "لغو رستوران"
    db.session.commit()
    return jsonify({"message": "سفارش لغو شد"}), 200

@seller_api_bp.route("/seller/orders/total", methods=["GET"])
@token_required_seller
def get_seller_total_orders():
    completed_orders = Order.query.filter_by(seller_id=request.seller.id, status="سفارش شما تکمیل شد").all()
    total_sales = sum(order.total_price for order in completed_orders)
    return jsonify({
        "completed_count": len(completed_orders),
        "total_sales": float(total_sales)
    }), 200
