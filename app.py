from flask import Flask, request, jsonify
from models import db, User, Seller, Food, Order, OrderDetail,Comment
from auth import register_user, register_seller, login_user, login_seller, token_required_seller, token_required_user
from flask_cors import CORS
from base64 import b64decode
import json
import os
import ast
from werkzeug.utils import secure_filename
import jdatetime


UPLOAD_FOLDER = 'static/upload'  # مسیر ذخیره تصاویر
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


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


# ویرایش کاربر شهر و رمزعبور
@app.route("/user/edit/password", methods=["POST"])
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


@app.route("/user/edit/city", methods=["POST"])
@token_required_user
def edit_user_city():
    data = request.json
    new_city = data.get("new_city_name")

    if not new_city:
        return jsonify({"success": False}), 400

    user = User.query.get_or_404(request.user.id)
    user.city_name = new_city
    db.session.commit()
    return jsonify({"success": True}), 200


# ویرایش فروشنده شهر و رمزعبور
@app.route("/seller/edit/password", methods=["POST"])
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


@app.route("/seller/edit/city", methods=["POST"])
@token_required_seller
def edit_seller_city():
    data = request.json
    new_city = data.get("new_city_name")

    if not new_city:
        return jsonify({"success": False}), 400

    seller = Seller.query.get_or_404(request.seller.id)
    seller.city_name = new_city
    db.session.commit()
    return jsonify({"success": True}), 200

@app.route("/seller/banner", methods=["GET"])
@token_required_seller
def get_restaurant_banner():
    seller = Seller.query.get_or_404(request.seller.id)
    return jsonify({"success": True, "img": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg"}), 200

@app.route("/seller/banner/update", methods=["PUT"])
@token_required_seller
def edit_restaurant_banner():
    data = request.json
    seller = Seller.query.get_or_404(request.seller.id)
    photo_data = data.get("photo")
    if photo_data:
        try:
            image_data = b64decode(photo_data.split(",")[-1])
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            image_filename = secure_filename(f"{seller.restaurant_name}_image.jpg")
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
    else:
        image_path = None

    seller.image = image_path
    db.session.commit()

    return jsonify({"success": True, "img": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg"}), 200



# تمامی فروشگاه های اطراف
@app.route("/user/restaurants", methods=["GET"])
@token_required_user
def get_restaurants():
    user = User.query.get_or_404(request.user.id)
    sellers = Seller.query.filter_by(city_name=user.city_name).all()

    restaurants = [
        {
            "id": seller.id,
            "name": seller.restaurant_name,
            "category": seller.category,
            "address": seller.address,
            "open": seller.open,
            "image": seller.image.replace("\\", "/") if seller.image else "static/banner/order-no-cost.jpg"
        }
        for seller in sellers
        if seller.open and Food.query.filter_by(seller_id=seller.id).first()  # Check if the seller is open and has foods
    ]

    return jsonify({"success": True, "restaurants": restaurants}), 200



@app.route("/user/restaurant/<int:id>", methods=["GET"])
@token_required_user
def get_restaurant_by_id(id):
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
        "foods": [  # List of food dictionaries
            {
                "food_id": food.id,
                "food_name": food.name,
                "food_price": food.price,
                "food_availability": food.availability,
                "food_description": food.description,
                "food_image": food.photo.replace("\\", "/"),
            }
            for food in seller_foods
        ],"comments": [  # List of food dictionaries
            {
                "comment_id": comment.id,
                "comment_content": comment.content,
                "comment_user_id": comment.user_id,
                "comment_seller_id": comment.seller_id,
            }
            for comment in seller_comments
        ]
    }
    return jsonify({"success": True, "restaurants": restaurants}), 200


#کامنت های کاربران
@app.route('/add/comment', methods=['POST'])
@token_required_user
def add_comment():
    user = User.query.get_or_404(request.user.id)
    seller_id = request.json.get('seller_id')
    content = request.json.get('content')


    new_comment = Comment(
        user_id=user.id,
        seller_id=seller_id,
        content=content
    )
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({'message': 'نظر با موفقیت افزوده شد'}), 201

@app.route('/comment/delete/<int:comment_id>', methods=['DELETE'])
@token_required_user
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)

    if not comment:
        return jsonify({'error': 'نظر یافت نشد'}), 404

    db.session.delete(comment)
    db.session.commit()

    return jsonify({'message': 'نظر با موفقیت حذف شد'}), 200

@app.route('/comments/<int:seller_id>', methods=['GET'])
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
            'created_at': comment.created_at
        })

    return jsonify(result), 200


# بررسی نوع فایل مجاز
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# تغییر وضعیت فروشگاه

@app.route("/seller/open", methods=["POST"])
@token_required_seller
def seller_edit_open():
    data = request.json
    open_seller = data.get("open")
    seller = Seller.query.get_or_404(request.seller.id)
    seller.open = open_seller
    db.session.commit()
    return jsonify({"success": True, "seller_open": seller.open}), 200

@app.route("/seller/open/status", methods=["GET"])
@token_required_seller
def seller_open_status():
    seller = Seller.query.get_or_404(request.seller.id)
    return jsonify({"success": True, "seller_open": seller.open}), 200


# اپلود تصویر فروشنده
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
@app.route("/seller/foods", methods=["POST"])
@token_required_seller
def add_food():
    data = request.json

    # Check for required fields
    if not all(key in data for key in ["name", "photo", "description", "price"]):
        return jsonify({"error": "Missing required fields"}), 400

    photo_data = data.get("photo")
    if photo_data:
        try:
            # Decode base64 image data
            image_data = b64decode(photo_data.split(",")[-1])

            # Create directory if it doesn't exist
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)

            # Generate a secure file name
            image_filename = secure_filename(f"{data['name']}_image.jpg")
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)

            # Save the image
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
        except Exception as e:
            return jsonify({"error": f"Invalid image data: {str(e)}"}), 400
    else:
        image_path = None

    # Create the Food instance
    food = Food(
        seller_id=request.seller.id,
        name=data["name"],
        photo=image_path,  # Save the file path in the database
        description=data["description"],
        price=data["price"],
        availability=data.get("availability", True)
    )
    db.session.add(food)
    db.session.commit()

    return jsonify({"message": "غذا اضافه شد.", "food_id": food.id}), 201

@app.route("/seller/food/<int:id>", methods=["GET"])
@token_required_seller
def get_food(id):
    food = Food.query.get_or_404(id)  # Filter by seller_id
    return jsonify({
        "foods": {
            "id": food.id,
            "name": food.name,
            "description": food.description,
            "price": food.price,
            "photo": food.photo.replace("\\", "/"),
            "availability": food.availability,
            "seller_id": food.seller_id
        },
        "success": "true"
    }), 200

@app.route("/seller/foods", methods=["GET"])
@token_required_seller
def get_foods():
    foods = Food.query.filter_by(seller_id=request.seller.id).all()  # Filter by seller_id
    return jsonify({
        "foods": [{
            "id": food.id,
            "name": food.name,
            "description": food.description,
            "price": food.price,
            "photo": food.photo.replace("\\", "/"),
            "availability": food.availability,
            "seller_id": food.seller_id
        } for food in foods],
        "success": "true"
    }), 200




@app.route("/seller/food/<int:food_id>", methods=["PUT"])
@token_required_seller
def update_food(food_id):
    data = request.json
    # Check if the food exists
    food = Food.query.filter_by(id=food_id, seller_id=request.seller.id).first()
    if not food:
        return jsonify({"error": "غذا پیدا نشد."}), 404

    # Check for required fields
    if not any(key in data for key in ["name", "photo", "description", "price", "availability"]):
        return jsonify({"error": "لطفا حداقل یک فیلد برای بروزرسانی ارسال کنید."}), 400

    # Update photo if provided
    if "photo" in data:
        photo_data = data["photo"]
        if photo_data:
            try:
                # Decode base64 image data
                image_data = b64decode(photo_data.split(",")[-1])

                # Create directory if it doesn't exist
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                # Generate a secure file name
                image_filename = secure_filename(f"{food.name}_image.jpg")
                image_path = os.path.join(UPLOAD_FOLDER, image_filename)

                # Save the image
                with open(image_path, "wb") as image_file:
                    image_file.write(image_data)

                # Update the food's photo path
                food.photo = image_path
            except Exception as e:
                return jsonify({"error": f"Invalid image data: {str(e)}"}), 400

    # Update other fields
    if "name" in data:
        food.name = data["name"]
    if "description" in data:
        food.description = data["description"]
    if "price" in data:
        food.price = data["price"]
    if "availability" in data:
        food.availability = data["availability"]

    # Commit the changes
    db.session.commit()

    return jsonify({"message": "غذا با موفقیت بروزرسانی شد.", "food_id": food.id}), 200


@app.route("/seller/foods/<int:food_id>", methods=["DELETE"])
@token_required_seller
def delete_food(food_id):
    """Delete a food item."""
    food = Food.query.get_or_404(food_id)

    # Check if the food belongs to the current seller
    if food.seller_id != request.seller.id:
        return jsonify({"message": "شما مجاز به حذف این غذا نیستید."}), 403

    db.session.delete(food)
    db.session.commit()
    return jsonify({"message": "غذا حذف شد."}), 200

# CRUD سفارشات
@app.route("/add/order", methods=["POST"])
@token_required_user
def place_order():
    """افزودن سفارش جدید"""
    user = User.query.get_or_404(request.user.id)  # گرفتن اطلاعات کاربر از توکن
    data = request.json
    # بررسی اطلاعات ورودی
    if not data.get("seller_id") or not data.get("details"):
        return jsonify({"message": "اطلاعات سفارش ناقص است."}), 400

    try:
        # تبدیل رشته به لیست با ast.literal_eval
        details = ast.literal_eval(data["details"])
    except (ValueError, SyntaxError):
        return jsonify({"message": "فرمت جزئیات سفارش نامعتبر است."}), 400

    # بررسی صحت ساختار داده‌ها
    if not isinstance(details, list) or not all(isinstance(item, (list, tuple)) and len(item) == 2 for item in details):
        return jsonify({"message": "فرمت جزئیات سفارش باید لیستی از جفت‌ها باشد."}), 400

    # تبدیل مقادیر به int (در صورت رشته بودن)
    try:
        details = [(int(item[0]), int(item[1])) for item in details]
    except ValueError:
        return jsonify({"message": "تمام مقادیر باید عددی باشند."}), 400

    # محاسبه مجموع قیمت
    total_price = 0
    for item in details:
        food = Food.query.get(item[0])  # food_id از جفت (food_id, quantity)
        if not food or not food.availability:
            return jsonify({"message": f"غذا با آی‌دی {item[0]} موجود نیست."}), 400

        # Check if food.price is a number (either int or float)
        try:
            price = float(food.price)  # Convert to float if it's a string
        except ValueError:
            return jsonify({"message": f"قیمت غذا با آی‌دی {item[0]} معتبر نیست."}), 400

        # Ensure item[1] is an integer (quantity)
        if not isinstance(item[1], int):
            return jsonify({"message": f"تعداد برای غذا با آی‌دی {item[0]} باید عدد صحیح باشد."}), 400

        total_price += price * item[1]  # قیمت * تعداد

    # ایجاد سفارش جدید
    new_order = Order(
        user_id=user.id,  # استفاده از user_id از توکن
        seller_id=data["seller_id"],
        total_price=total_price,
        status="تایید رستوران"
    )
    db.session.add(new_order)
    db.session.commit()

    # اضافه کردن جزئیات سفارش
    for item in details:
        food = Food.query.get(item[0])  # Get food only once
        if food:
            order_detail = OrderDetail(
                order_id=new_order.id,
                food_id=item[0],  # food_id
                quantity=item[1],  # quantity
                price=food.price  # قیمت غذا
            )
            db.session.add(order_detail)
        else:
            return jsonify({"message": f"غذا با آی‌دی {item[0]} پیدا نشد."}), 400
    db.session.commit()

    return jsonify({"message": "سفارش با موفقیت ثبت شد.", "order_id": new_order.id}), 201


@app.route("/user/orders", methods=["GET"])
@token_required_user
def get_user_orders():
    """دریافت لیست سفارش‌های کاربر"""
    orders = Order.query.filter(
        Order.user_id == request.user.id,
        Order.status != "سفارش شما تکمیل شد",
        Order.status != "لغو رستوران",
        Order.status != "لغو کاربر"
    ).all()

    
    # تبدیل سفارش‌ها به فرمت JSON
    return jsonify([{
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": Seller.query.get(order.seller_id).restaurant_name if Seller.query.get(order.seller_id) else "نامشخص",
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),  # تبدیل به float برای JSON
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "quantity": detail.quantity,
            "price": float(detail.price)  # تبدیل به float برای JSON
        } for detail in order.details]
    } for order in orders]), 200


@app.route("/user/orders/all", methods=["GET"])
@token_required_user
def get_user_orders_all():
    """دریافت لیست سفارش‌های کاربر"""
    orders = Order.query.filter(
        Order.user_id == request.user.id).all()


    # تبدیل سفارش‌ها به فرمت JSON
    return jsonify([{
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": Seller.query.get(order.seller_id).restaurant_name if Seller.query.get(order.seller_id) else "نامشخص",
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),  # تبدیل به float برای JSON
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "quantity": detail.quantity,
            "price": float(detail.price)  # تبدیل به float برای JSON
        } for detail in order.details]
    } for order in orders]), 200


@app.route("/user/orders/<int:order_id>", methods=["GET"])
@token_required_user
def get_user_order(order_id):
    """دریافت جزئیات یک سفارش بر اساس آی‌دی"""
    # پیدا کردن سفارش بر اساس آی‌دی و کاربر
    order = Order.query.filter_by(id=order_id, user_id=request.user.id).first()
    if not order:
        return jsonify({"message": "سفارش پیدا نشد."}), 404

    # اطلاعات فروشنده
    seller = Seller.query.get(order.seller_id)
    seller_name = seller.restaurant_name if seller else "نامشخص"

    # جمع‌بندی تعداد غذاها
    total_items = sum(detail.quantity for detail in order.details)

    # ساختن پاسخ
    response = {
        "id": order.id,
        "seller_id": order.seller_id,
        "seller_name": seller_name,
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),  # تبدیل به float برای JSON
        "total_items": total_items,  # تعداد کل غذاها
        "status": order.status,
        "details": [{
            "food_id": detail.food_id,
            "food_name": Food.query.get(detail.food_id).name ,
            "food_img": Food.query.get(detail.food_id).photo.replace("\\", "/") ,
            "quantity": detail.quantity,
            "price": float(detail.price)  # تبدیل به float برای JSON
        } for detail in order.details]
    }

    return jsonify(response), 200

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


@app.route("/user/orders/cancel/<int:order_id>", methods=["PUT"])
@token_required_user
def cancel_order(order_id):
    """لغو سفارش"""
    # پیدا کردن سفارش بر اساس آی‌دی و کاربر
    order = Order.query.filter_by(id=order_id, user_id=request.user.id).first()

    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه لغو آن را ندارید."}), 404

    # تغییر وضعیت سفارش به "لغو"
    order.status = "لغو کاربر"

    try:
        # ذخیره تغییرات
        db.session.commit()
        return jsonify({"message": "سفارش با موفقیت لغو شد.", "order_id": order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطا در لغو سفارش.", "error": str(e)}), 500


@app.route("/seller/orders/not", methods=["GET"])
@token_required_seller
def get_seller_orders_not_finish():
    """دریافت سفارش‌های یک فروشنده که هنوز تکمیل نشده‌اند"""
    # دریافت seller_id از توکن
    seller_id = request.seller.id

    # گرفتن سفارش‌هایی که هنوز تکمیل نشده‌اند (وضعیت غیر از "سفارش شما تکمیل شد")

    orders = Order.query.filter(
        Order.seller_id == seller_id,
        Order.status != "سفارش شما تکمیل شد",
        Order.status != "لغو رستوران",
        Order.status != "لغو کاربر"
    ).all()

    # ساختن پاسخ
    response = []
    for order in orders:
        # اطلاعات کاربر سفارش‌دهنده
        user = User.query.get(order.user_id)
        user_name = user.name if user else "نامشخص"
        user_address = user.address if user else "آدرس نامشخص"

        # جمع‌بندی تعداد غذاها
        total_items = sum(detail.quantity for detail in order.details)

        # لیست غذاها و تعداد آنها
        food_details = [{
            "food_name": Food.query.get(detail.food_id).name,
            "quantity": detail.quantity
        } for detail in order.details]

        # اطلاعات سفارش
        order_data = {
            "order_id": order.id,
            "user_id": order.user_id,
            "user_name": user_name,
            "user_address": user_address,
            "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
            "total_price": float(order.total_price),
            "total_items": total_items,
            "status": order.status,
            "food_details": food_details
        }

        response.append(order_data)

    return jsonify(response), 200



@app.route("/seller/orders/all", methods=["GET"])
@token_required_seller
def get_seller_orders():
    """دریافت سفارش‌های یک فروشنده که هنوز تکمیل نشده‌اند"""
    # دریافت seller_id از توکن
    seller_id = request.seller.id

    # گرفتن سفارش‌هایی که هنوز تکمیل نشده‌اند (وضعیت غیر از "سفارش شما تکمیل شد")
    orders = Order.query.filter(Order.seller_id == seller_id).all()

    # ساختن پاسخ
    response = []
    for order in orders:
        # اطلاعات کاربر سفارش‌دهنده
        user = User.query.get(order.user_id)
        user_name = user.name if user else "نامشخص"
        user_address = user.address if user else "آدرس نامشخص"

        # جمع‌بندی تعداد غذاها
        total_items = sum(detail.quantity for detail in order.details)

        # لیست غذاها و تعداد آنها
        food_details = [{
            "food_name": Food.query.get(detail.food_id).name,
            "quantity": detail.quantity
        } for detail in order.details]

        # اطلاعات سفارش
        order_data = {
            "order_id": order.id,
            "user_id": order.user_id,
            "user_name": user_name,
            "user_address": user_address,
            "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
            "total_price": float(order.total_price),
            "total_items": total_items,
            "status": order.status,
            "food_details": food_details
        }

        response.append(order_data)

    return jsonify(response), 200


@app.route("/seller/orders/detail/<int:order_id>", methods=["GET"])
@token_required_seller
def get_seller_order_details(order_id):

    # دریافت seller_id از توکن
    seller_id = request.seller.id

    # پیدا کردن سفارش بر اساس order_id و seller_id
    order = Order.query.filter_by(id=order_id, seller_id=seller_id).first()

    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه دسترسی ندارید."}), 404

    # اطلاعات کاربر سفارش‌دهنده
    user = User.query.get(order.user_id)
    user_name = user.name if user else "نامشخص"
    user_address = user.address if user else "آدرس نامشخص"

    # جمع‌بندی تعداد غذاها
    total_items = sum(detail.quantity for detail in order.details)

    # لیست غذاها و تعداد آنها
    food_details = [{
        "food_name": Food.query.get(detail.food_id).name,
        "food_img": Food.query.get(detail.food_id).photo.replace("\\", "/"),
        "quantity": detail.quantity,
        "price": Food.query.get(detail.food_id).price
    } for detail in order.details]

    # اطلاعات سفارش
    order_data = {
        "order_id": order.id,
        "user_id": order.user_id,
        "user_name": user_name,
        "user_address": user_address,
        "order_date": jdatetime.datetime.fromgregorian(datetime=order.order_date).strftime("%Y-%m-%d %H:%M:%S"),
        "total_price": float(order.total_price),
        "total_items": total_items,
        "status": order.status,
        "food_details": food_details
    }

    return jsonify(order_data), 200



@app.route("/seller/orders/preparing/<int:order_id>", methods=["PUT"])
@token_required_seller
def preparing_order(order_id):
    """تغییر وضعیت سفارش به 'در حال آماده سازی'"""
    # پیدا کردن سفارش بر اساس آی‌دی و کاربر
    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه تغییر وضعیت آن را ندارید."}), 404

    # تغییر وضعیت سفارش به "در حال آماده سازی"
    order.status = "در حال آماده سازی"

    try:
        # ذخیره تغییرات
        db.session.commit()
        return jsonify({"message": "سفارش به وضعیت 'در حال آماده سازی' تغییر کرد.", "order_id": order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطا در تغییر وضعیت سفارش.", "error": str(e)}), 500


@app.route("/seller/orders/completed/<int:order_id>", methods=["PUT"])
@token_required_seller
def completed_order(order_id):
    """تغییر وضعیت سفارش به 'سفارش شما تکمیل شد'"""
    # پیدا کردن سفارش بر اساس آی‌دی و کاربر
    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه تغییر وضعیت آن را ندارید."}), 404

    # تغییر وضعیت سفارش به "سفارش شما تکمیل شد"
    order.status = "سفارش شما تکمیل شد"

    try:
        # ذخیره تغییرات
        db.session.commit()
        return jsonify({"message": "سفارش به وضعیت 'سفارش شما تکمیل شد' تغییر کرد.", "order_id": order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطا در تغییر وضعیت سفارش.", "error": str(e)}), 500


@app.route("/seller/orders/cancel/<int:order_id>", methods=["PUT"])
@token_required_seller
def seller_cancel_order(order_id):
    """لغو سفارش"""
    # پیدا کردن سفارش بر اساس آی‌دی و کاربر
    order = Order.query.filter_by(id=order_id).first()

    if not order:
        return jsonify({"message": "سفارش پیدا نشد یا شما اجازه لغو آن را ندارید."}), 404

    # تغییر وضعیت سفارش به "لغو"
    order.status = "لغو رستوران"

    try:
        # ذخیره تغییرات
        db.session.commit()
        return jsonify({"message": "سفارش با موفقیت لغو شد.", "order_id": order.id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "خطا در لغو سفارش.", "error": str(e)}), 500


@app.route("/seller/orders/total", methods=["GET"])
@token_required_seller
def get_seller_total_orders():
    # دریافت seller_id از توکن
    seller_id = request.seller.id

    # گرفتن سفارش‌های تکمیل شده برای فروشنده
    completed_orders = Order.query.filter(
        Order.seller_id == seller_id,
        Order.status == "سفارش شما تکمیل شد"
    ).all()

    # گرفتن سفارش‌های لغو شده برای فروشنده
    canceled_orders = Order.query.filter(
        Order.seller_id == seller_id,
        Order.status.in_(["لغو رستوران", "لغو کاربر"])
    ).all()

    # جمع کردن total_price از تمامی سفارش‌های تکمیل شده
    total_price = sum(order.total_price for order in completed_orders)

    # شمارش تعداد سفارش‌های تکمیل شده و لغو شده
    completed_count = len(completed_orders)
    canceled_count = len(canceled_orders)

    # ساختن پاسخ به صورت JSON
    response = {
        "message": "جمع تمامی قیمت‌های سفارش‌ها برای فروشنده",
        "total_price": int(total_price),
        "completed_orders_count": completed_count,
        "canceled_orders_count": canceled_count
    }

    return jsonify(response), 200


@app.route("/user/orders/total", methods=["GET"])
@token_required_user
def get_user_total_orders():
    user_id=request.user.id
    """جمع تمامی قیمت‌های سفارش‌های یک کاربر و شمارش سفارش‌های تکمیل شده و لغو شده"""
    # گرفتن سفارش‌های تکمیل شده برای کاربر
    completed_orders = Order.query.filter(
        Order.user_id == user_id,
        Order.status == "سفارش شما تکمیل شد"
    ).all()

    # گرفتن سفارش‌های لغو شده برای کاربر
    canceled_orders = Order.query.filter(
        Order.user_id == user_id,
        Order.status.in_(["لغو رستوران", "لغو کاربر"])
    ).all()

    # جمع کردن total_price از تمامی سفارش‌های تکمیل شده
    total_price = sum(order.total_price for order in completed_orders)

    # شمارش تعداد سفارش‌های تکمیل شده و لغو شده
    completed_count = len(completed_orders)
    canceled_count = len(canceled_orders)

    # ساختن پاسخ به صورت JSON
    response = {
        "message": "جمع تمامی قیمت‌های سفارش‌ها برای کاربر",
        "total_price": int(total_price),
        "completed_orders_count": completed_count,
        "canceled_orders_count": canceled_count
    }

    return jsonify(response), 200


# راه‌اندازی سرور
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # ایجاد جداول در پایگاه‌داده
    app.run(debug=True)
