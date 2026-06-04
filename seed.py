from app import create_app
from models import db, User, Seller, Food, Order, OrderDetail, Comment, Admin
from datetime import datetime

def seed_data():
    app = create_app()
    with app.app_context():
        # Clean existing data
        db.drop_all()
        db.create_all()

        # Add Admin
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Add Users
        u1 = User(name="دانیال", phone="09121111111", city_name="تهران", address="سعادت آباد", latitude=35.77, longitude=51.35)
        u1.set_password("user123")
        u2 = User(name="سارا", phone="09122222222", city_name="اصفهان", address="خیابان نظر", latitude=32.65, longitude=51.66)
        u2.set_password("user123")
        db.session.add_all([u1, u2])

        # Add Sellers
        s1 = Seller(
            restaurant_name="پیتزا دانیال",
            phone="09123333333",
            city_name="تهران",
            category="پیتزا و فست فود",
            address="ونک",
            latitude=35.75,
            longitude=51.40,
            open=True,
            image="static/banner/pizza.jpg"
        )
        s1.set_password("seller123")

        s2 = Seller(
            restaurant_name="کباب سرای ریحون",
            phone="09124444444",
            city_name="تهران",
            category="ایرانی",
            address="نیاوران",
            latitude=35.80,
            longitude=51.45,
            open=True,
            image="static/banner/kebab.jpg"
        )
        s2.set_password("seller123")
        db.session.add_all([s1, s2])
        db.session.flush()

        # Add Foods
        f1 = Food(seller_id=s1.id, name="پیتزا پپرونی", price="250000", description="تند و لذیذ با کالباس درجه یک", availability=True, photo="static/food/pepperoni.jpg")
        f2 = Food(seller_id=s1.id, name="سیب زمینی سرخ کرده", price="95000", description="با ادویه مخصوص و سس کچاپ", availability=True, photo="static/food/fries.jpg")
        f3 = Food(seller_id=s2.id, name="چلو کباب کوبیده", price="320000", description="دو سیخ کباب لقمه با برنج ایرانی", availability=True, photo="static/food/chelow.jpg")
        db.session.add_all([f1, f2, f3])
        db.session.flush()

        # Add Comments
        c1 = Comment(user_id=u1.id, seller_id=s1.id, content="پیتزای خیلی خوشمزه‌ای بود، گرم رسید و کیفیت عالی بود.", rating=5)
        c2 = Comment(user_id=u2.id, seller_id=s1.id, content="کمی دیر رسید ولی طعمش واقعا خوب بود.", rating=4)
        c3 = Comment(user_id=u1.id, seller_id=s2.id, content="کباب‌ها فوق‌العاده بودند، برنج هم کاملا ایرانی بود.", rating=5)
        db.session.add_all([c1, c2, c3])

        # Add Orders
        o1 = Order(user_id=u1.id, seller_id=s1.id, total_price=345000, status="سفارش شما تکمیل شد")
        db.session.add(o1)
        db.session.flush()

        od1 = OrderDetail(order_id=o1.id, food_id=f1.id, quantity=1, price=250000)
        od2 = OrderDetail(order_id=o1.id, food_id=f2.id, quantity=1, price=95000)
        db.session.add_all([od1, od2])

        db.session.commit()
        print("Database seeded successfully with images!")

if __name__ == "__main__":
    seed_data()
