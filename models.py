from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

# مدل مدیران سیستم
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    token = db.Column(db.String(200), unique=True, nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# مدل کاربران
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    city_name = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(200), unique=True, nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

# مدل فروشندگان
class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(100), nullable=False)
    open = db.Column(db.Boolean, nullable=False, default=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    city_name = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    address = db.Column(db.Text, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    image = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    token = db.Column(db.String(200), unique=True, nullable=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def average_rating(self):
        from sqlalchemy import func
        result = db.session.query(func.avg(Comment.rating)).filter(Comment.seller_id == self.id).scalar()
        return round(float(result), 1) if result else 5.0

    @property
    def total_ratings(self):
        return Comment.query.filter_by(seller_id=self.id).count()

# مدل غذاها
class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    photo = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Text, nullable=False)
    availability = db.Column(db.Boolean, default=True)
    seller = db.relationship('Seller', backref=db.backref('foods', lazy=True))

# مدل سفارشات
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Text, default="در انتظار تایید رستوران")
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    seller = db.relationship('Seller', backref=db.backref('orders', lazy=True))

# مدل جزئیات سفارشات
class OrderDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    order = db.relationship('Order', backref=db.backref('details', lazy=True))
    food = db.relationship('Food', backref=db.backref('order_details', lazy=True))

# مدل نظرات
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('comments', lazy=True))
    seller = db.relationship('Seller', backref=db.backref('comments', lazy=True))
