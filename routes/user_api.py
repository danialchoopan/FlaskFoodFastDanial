from flask import Blueprint, request, jsonify
from models import db, User, Seller, Food, Order, OrderDetail, Comment
from routes.auth_routes import token_required_user
from utils.order_status import OrderStatus
import ast
import jdatetime
from datetime import datetime
import math

user_api_bp = Blueprint('user_api', __name__)

@user_api_bp.route("/user/edit/password", methods=["POST"])
@token_required_user
def edit_user_password():
    data = request.json
    new_password = data.get("new_password")
    old_password = data.get("old_password")
    user = User.query.get_or_404(request.user.id)
    if not user.check_password(old_password):
        return jsonify({"success": False, "message": "رمزعبور وارد شده شما اشتباه است"}), 400
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"success": True}), 200

@user_api_bp.route("/user/edit/city", methods=["POST"])
@token_required_user
def edit_user_city():
    data = request.json
    new_city = data.get("new_city_name")
    if not new_city:
        return jsonify({"success": False}), 400
    user = User.query.get_or_404(request.user.id)
    user.city_name = new_city
    if "latitude" in data: user.latitude = data["latitude"]
    if "longitude" in data: user.longitude = data["longitude"]
    db.session.commit()
    return jsonify({"success": True}), 200

@user_api_bp.route("/user/update_location", methods=["POST"])
@token_required_user
def update_location():
    data = request.json
    user = User.query.get_or_404(request.user.id)
    if "latitude" in data: user.latitude = data["latitude"]
    if "longitude" in data: user.longitude = data["longitude"]
    if "address" in data: user.address = data["address"]
    db.session.commit()
    return jsonify({"success": True, "message": "موقعیت جغرافیایی بروزرسانی شد"}), 200

@user_api_bp.route("/user/restaurants", methods=["GET"])
@token_required_user
def get_restaurants():
    """Get list of restaurants in user's city.
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of open restaurants with food items
      401:
        description: Invalid or missing token
    """
    user = User.query.get_or_404(request.user.id)
    sellers = Seller.query.filter_by(city_name=user.city_name, is_active=True).all()
    restaurants = [
        {
            "id": seller.id,
            "name": seller.restaurant_name,
            "category": seller.category,
            "address": seller.address,
            "open": seller.open,
            "image": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg",
            "rating": seller.average_rating
        }
        for seller in sellers
        if seller.open and Food.query.filter_by(seller_id=seller.id).first()
    ]
    return jsonify({"success": True, "restaurants": restaurants}), 200

@user_api_bp.route("/user/restaurant/<int:id>", methods=["GET"])
@token_required_user
def get_restaurant_by_id(id):
    """Get restaurant details with menu and comments.
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Restaurant details with foods and comments
    """
    seller = Seller.query.get_or_404(id)
    seller_foods = Food.query.filter_by(seller_id=seller.id).all()
    seller_comments = Comment.query.filter_by(seller_id=seller.id).all()
    restaurants = {
        "seller_id": seller.id,
        "restaurant_name": seller.restaurant_name,
        "restaurant_category": seller.category,
        "restaurant_address": seller.address,
        "restaurant_open": seller.open,
        "restaurant_image": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg",
        "foods": [
            {
                "food_id": food.id,
                "food_name": food.name,
                "food_price": food.price,
                "food_availability": food.availability,
                "food_description": food.description,
                "food_image": food.photo.replace("\\", "/") if food.photo else "",
            }
            for food in seller_foods
        ],
        "comments": [
            {
                "comment_id": comment.id,
                "comment_content": comment.content,
                "comment_user_id": comment.user_id,
                "comment_seller_id": comment.seller_id,
                "comment_rating": comment.rating
            }
            for comment in seller_comments
        ]
    }
    return jsonify({"success": True, "restaurants": restaurants}), 200

@user_api_bp.route('/add/comment', methods=['POST'])
@token_required_user
def add_comment():
    """Add a comment/review for a restaurant.
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [seller_id, content]
            properties:
              seller_id:
                type: integer
              content:
                type: string
              rating:
                type: integer
                minimum: 1
                maximum: 5
                default: 5
    responses:
      201:
        description: Comment added
    """
    user = User.query.get_or_404(request.user.id)
    seller_id = request.json.get('seller_id')
    content = request.json.get('content')
    rating = request.json.get('rating', 5)
    new_comment = Comment(
        user_id=user.id,
        seller_id=seller_id,
        content=content,
        rating=rating
    )
    db.session.add(new_comment)
    db.session.commit()
    return jsonify({'message': 'نظر با موفقیت افزوده شد'}), 201

@user_api_bp.route('/comment/delete/<int:comment_id>', methods=['DELETE'])
@token_required_user
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({'error': 'نظر یافت نشد'}), 404
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'message': 'نظر با موفقیت حذف شد'}), 200

@user_api_bp.route('/comments/<int:seller_id>', methods=['GET'])
@token_required_user
def get_comments(seller_id):
    comments = Comment.query.filter_by(seller_id=seller_id).all()
    if not comments:
        return jsonify({'message': 'نظری برای این فروشنده یافت نشد'}), 404
    result = []
    for comment in comments:
        result.append({
            'id': comment.id,
            'user_id': comment.user_id,
            'content': comment.content,
            'rating': comment.rating,
            'created_at': comment.created_at
        })
    return jsonify(result), 200

@user_api_bp.route("/add/order", methods=["POST"])
@token_required_user
def place_order():
    """Place a new order.
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required: [seller_id, details]
            properties:
              seller_id:
                type: integer
              details:
                type: string
                description: "Stringified list of [food_id, quantity] pairs, e.g. '[[1, 2], [3, 1]]'"
    responses:
      201:
        description: Order placed successfully
      400:
        description: Invalid order data
    """
    user = User.query.get_or_404(request.user.id)
    data = request.json
    if not data.get("seller_id") or not data.get("details"):
        return jsonify({"message": "اطلاعات سفارش ناقص است."}), 400
    try:
        details = ast.literal_eval(data["details"])
    except (ValueError, SyntaxError):
        return jsonify({"message": "فرمت جزئیات سفارش نامعتبر است."}), 400
    if not isinstance(details, list) or not all(isinstance(item, (list, tuple)) and len(item) == 2 for item in details):
        return jsonify({"message": "فرمت جزئیات سفارش باید لیستی از جفت‌ها باشد."}), 400
    try:
        details = [(int(item[0]), int(item[1])) for item in details]
    except ValueError:
        return jsonify({"message": "تمام مقادیر باید عددی باشند."}), 400
    total_price = 0
    for item in details:
        food = Food.query.get(item[0])
        if not food or not food.availability:
            return jsonify({"message": f"غذا با آی‌دی {item[0]} موجود نیست."}), 400
        try:
            price = float(food.price)
        except ValueError:
            return jsonify({"message": f"قیمت غذا با آی‌دی {item[0]} معتبر نیست."}), 400
        total_price += price * item[1]
    new_order = Order(
        user_id=user.id,
        seller_id=data["seller_id"],
        total_price=total_price,
        status=OrderStatus.CONFIRMED
    )
    db.session.add(new_order)
    db.session.commit()
    for item in details:
        food = Food.query.get(item[0])
        if food:
            order_detail = OrderDetail(
                order_id=new_order.id,
                food_id=item[0],
                quantity=item[1],
                price=food.price
            )
            db.session.add(order_detail)
    db.session.commit()
    return jsonify({"message": "سفارش با موفقیت ثبت شد.", "order_id": new_order.id}), 201

@user_api_bp.route("/user/orders", methods=["GET"])
@token_required_user
def get_user_orders():
    """Get user's active orders (excluding completed/cancelled).
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    responses:
      200:
        description: List of active orders
    """
    orders = Order.query.filter(
        Order.user_id == request.user.id,
        Order.status != OrderStatus.COMPLETED,
        Order.status != OrderStatus.CANCELLED_BY_SELLER,
        Order.status != OrderStatus.CANCELLED_BY_USER
    ).all()
    return jsonify([{
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": Seller.query.get(order.seller_id).restaurant_name if Seller.query.get(order.seller_id) else "نامشخص",
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "quantity": detail.quantity,
            "price": float(detail.price)
        } for detail in order.details]
    } for order in orders]), 200

@user_api_bp.route("/user/orders/all", methods=["GET"])
@token_required_user
def get_user_orders_all():
    orders = Order.query.filter(Order.user_id == request.user.id).all()
    return jsonify([{
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": Seller.query.get(order.seller_id).restaurant_name if Seller.query.get(order.seller_id) else "نامشخص",
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "quantity": detail.quantity,
            "price": float(detail.price)
        } for detail in order.details]
    } for order in orders]), 200

@user_api_bp.route("/user/orders/<int:order_id>", methods=["GET"])
@token_required_user
def get_user_order(order_id):
    order = Order.query.filter_by(id=order_id, user_id=request.user.id).first()
    if not order:
        return jsonify({"message": "سفارش پیدا نشد."}), 404
    seller = Seller.query.get(order.seller_id)
    seller_name = seller.restaurant_name if seller else "نامشخص"
    total_items = sum(detail.quantity for detail in order.details)
    response = {
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": seller_name,
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),
        "total_items": total_items,
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "food_name": Food.query.get(detail.food_id).name,
            "food_img": Food.query.get(detail.food_id).photo.replace("\\", "/") if Food.query.get(detail.food_id).photo else "",
            "quantity": detail.quantity,
            "price": float(detail.price)
        } for detail in order.details]
    }
    return jsonify(response), 200

@user_api_bp.route("/user/orders/cancel/<int:order_id>", methods=["PUT"])
@token_required_user
def cancel_order(order_id):
    """Cancel an order by the user.
    ---
    tags: [User API]
    security:
      - BearerAuth: []
    parameters:
      - in: path
        name: order_id
        required: true
        schema:
          type: integer
    responses:
      200:
        description: Order cancelled
      404:
        description: Order not found
    """
    order = Order.query.filter_by(id=order_id, user_id=request.user.id).first()
    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه لغو آن را ندارید."}), 404
    order.status = OrderStatus.CANCELLED_BY_USER
    try:
        db.session.commit()
        return jsonify({"message": "سفارش با موفقیت لغو شد.", "order_id": order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطا در لغو سفارش.", "error": str(e)}), 500

@user_api_bp.route("/user/orders/total", methods=["GET"])
@token_required_user
def get_user_total_orders():
    user_id = request.user.id
    completed_orders = Order.query.filter(Order.user_id == user_id, Order.status == OrderStatus.COMPLETED).all()
    canceled_orders = Order.query.filter(Order.user_id == user_id, Order.status.in_([OrderStatus.CANCELLED_BY_SELLER, OrderStatus.CANCELLED_BY_USER])).all()
    total_price = sum(order.total_price for order in completed_orders)
    completed_count = len(completed_orders)
    canceled_count = len(canceled_orders)
    response = {
        "message": "جمع تمامی قیمت‌های سفارش‌ها برای کاربر",
        "total_price": int(total_price),
        "completed_orders_count": completed_count,
        "canceled_orders_count": canceled_count
    }
    return jsonify(response), 200

@user_api_bp.route("/user/restaurants/nearby", methods=["GET"])
@token_required_user
def get_nearby_restaurants():
    user_lat = request.args.get('lat', type=float)
    user_lon = request.args.get('lon', type=float)
    if user_lat is None or user_lon is None:
        user = User.query.get(request.user.id)
        user_lat, user_lon = user.latitude, user.longitude
    if user_lat is None or user_lon is None:
        return jsonify({"success": False, "message": "موقعیت جغرافیایی یافت نشد"}), 400
    sellers = Seller.query.filter_by(is_active=True).all()
    def calculate_distance(lat1, lon1, lat2, lon2):
        if lat1 is None or lon1 is None or lat2 is None or lon2 is None: return float('inf')
        return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)
    nearby_sellers = sorted(sellers, key=lambda s: calculate_distance(user_lat, user_lon, s.latitude, s.longitude))
    restaurants = [
        {
            "id": seller.id,
            "name": seller.restaurant_name,
            "category": seller.category,
            "address": seller.address,
            "open": seller.open,
            "image": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg",
            "rating": seller.average_rating
        }
        for seller in nearby_sellers
    ]
    return jsonify({"success": True, "restaurants": restaurants}), 200
