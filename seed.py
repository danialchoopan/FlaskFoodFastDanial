from app import create_app
from models import db, User, Seller, Food, Order, OrderDetail, Comment, Admin, Setting
from utils.order_status import OrderStatus
from datetime import datetime, timedelta
import json


def seed_data():
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()

        # Admin
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)

        # Settings
        defaults = {
            'food_categories': json.dumps(["پیتزا", "فست فود", "ایرانی", "سالاد", "دسر", "نوشیدنی"]),
            'cities': json.dumps(["تهران", "اصفهان", "شیراز", "تبریز", "مشهد"]),
            'platform_fee_percent': '5',
        }
        for key, value in defaults.items():
            db.session.add(Setting(key=key, value=value))

        # Users
        users_data = [
            ("دانیال", "09121111111", "تهران", "سعادت آباد", 35.77, 51.35),
            ("سارا", "09122222222", "اصفهان", "خیابان نظر", 32.65, 51.66),
            ("محمد", "09123333333", "تهران", "ونک", 35.75, 51.40),
            ("زهرا", "09124444444", "تهران", "نیاوران", 35.80, 51.45),
            ("علی", "09125555555", "شیراز", "زند", 29.59, 52.58),
        ]
        users = []
        for name, phone, city, addr, lat, lon in users_data:
            u = User(name=name, phone=phone, city_name=city, address=addr, latitude=lat, longitude=lon)
            u.set_password("user123")
            users.append(u)
        db.session.add_all(users)
        db.session.flush()

        # Sellers with real banner images
        sellers_data = [
            ("پیتزا دانیال", "09126666666", "تهران", "پیتزا و فست فود", "ونک", 35.75, 51.40, True, "static/banner/pizza.jpg"),
            ("کباب سرای ریحون", "09127777777", "تهران", "ایرانی", "نیاوران", 35.80, 51.45, True, "static/banner/kebab.jpg"),
            ("سوپر برگر", "09128888888", "تهران", "فست فود", "سعادت آباد", 35.77, 51.35, True, "static/banner/burger.jpg"),
            ("رستوران سنتی نقش جهان", "09129999999", "اصفهان", "ایرانی", "نقش جهان", 32.65, 51.68, True, "static/banner/traditional.jpg"),
            ("چلوکبابی امیر", "09120000000", "شیراز", "ایرانی", "زند", 29.59, 52.58, False, "static/banner/kebabhouse.jpg"),
        ]
        sellers = []
        for name, phone, city, cat, addr, lat, lon, open_, banner in sellers_data:
            s = Seller(restaurant_name=name, phone=phone, city_name=city, category=cat,
                       address=addr, latitude=lat, longitude=lon, open=open_, image=banner)
            s.set_password("seller123")
            sellers.append(s)
        db.session.add_all(sellers)
        db.session.flush()

        # Foods with real images
        foods_data = [
            (sellers[0].id, "پیتزا پپرونی", 250000, "تند و لذیذ با کالباس درجه یک", "static/food/pepperoni.jpg"),
            (sellers[0].id, "سیب زمینی سرخ کرده", 95000, "با ادویه مخصوص و سس کچاپ", "static/food/fries.jpg"),
            (sellers[0].id, "پیتزا مخصوص", 320000, "با قارچ و فلفل دلمه", "static/food/pizza_mix.jpg"),
            (sellers[1].id, "چلو کباب کوبیده", 320000, "دو سیخ کباب لقمه با برنج ایرانی", "static/food/chelow.jpg"),
            (sellers[1].id, "چلو جوجه کباب", 280000, "جوجه کباب زعفرانی با برنج", "static/food/joojeh.jpg"),
            (sellers[1].id, "آش رشته", 85000, "آش سنتی اصفهان", "static/food/ash.jpg"),
            (sellers[2].id, "برگر کلاسیک", 180000, "گوشت گوساله با سس مخصوص", "static/food/burger.jpg"),
            (sellers[2].id, "سیب زمینی خلالی", 75000, "سیب زمینی خلالی با سس قرمز", "static/food/fries2.jpg"),
            (sellers[3].id, "باقلی پلو با گوشت", 260000, "باقلی پلو سنتی اصفهانی", "static/food/baghali.jpg"),
            (sellers[3].id, "قیمه نثار", 240000, "قیمه نثار اصیل اصفهان", "static/food/qeime.jpg"),
        ]
        foods = []
        for sid, name, price, desc, photo in foods_data:
            foods.append(Food(seller_id=sid, name=name, price=price, description=desc,
                              availability=True, photo=photo))
        db.session.add_all(foods)
        db.session.flush()

        # Orders with various statuses
        now = datetime.utcnow()
        orders_data = [
            (users[0].id, sellers[0].id, 345000, OrderStatus.COMPLETED, now - timedelta(days=5)),
            (users[1].id, sellers[0].id, 250000, OrderStatus.COMPLETED, now - timedelta(days=4)),
            (users[2].id, sellers[1].id, 600000, OrderStatus.PREPARING, now - timedelta(hours=2)),
            (users[0].id, sellers[1].id, 320000, OrderStatus.WAITING_CONFIRMATION, now - timedelta(hours=1)),
            (users[3].id, sellers[2].id, 255000, OrderStatus.COMPLETED, now - timedelta(days=3)),
            (users[4].id, sellers[3].id, 500000, OrderStatus.COMPLETED, now - timedelta(days=2)),
            (users[1].id, sellers[3].id, 240000, OrderStatus.CANCELLED_BY_USER, now - timedelta(days=1)),
            (users[2].id, sellers[2].id, 180000, OrderStatus.CANCELLED_BY_SELLER, now - timedelta(hours=6)),
            (users[0].id, sellers[0].id, 415000, OrderStatus.CONFIRMED, now - timedelta(minutes=30)),
        ]
        orders = []
        for uid, sid, total, status, odate in orders_data:
            o = Order(user_id=uid, seller_id=sid, total_price=total, status=status, order_date=odate)
            orders.append(o)
        db.session.add_all(orders)
        db.session.flush()

        # Order details
        detail_data = [
            (orders[0].id, foods[0].id, 1, 250000),
            (orders[0].id, foods[1].id, 1, 95000),
            (orders[1].id, foods[2].id, 1, 320000),
            (orders[2].id, foods[3].id, 2, 320000),
            (orders[3].id, foods[4].id, 1, 280000),
            (orders[4].id, foods[6].id, 1, 180000),
            (orders[4].id, foods[7].id, 1, 75000),
            (orders[5].id, foods[8].id, 1, 260000),
            (orders[5].id, foods[9].id, 1, 240000),
            (orders[8].id, foods[0].id, 1, 250000),
            (orders[8].id, foods[1].id, 1, 95000),
            (orders[8].id, foods[2].id, 1, 320000),
        ]
        for oid, fid, qty, price in detail_data:
            db.session.add(OrderDetail(order_id=oid, food_id=fid, quantity=qty, price=price))

        # Comments
        comments_data = [
            (users[0].id, sellers[0].id, "پیتزای خیلی خوشمزه‌ای بود، گرم رسید و کیفیت عالی بود.", 5),
            (users[1].id, sellers[0].id, "کمی دیر رسید ولی طعمش واقعا خوب بود.", 4),
            (users[0].id, sellers[1].id, "کباب‌ها فوق‌العاده بودند، برنج هم کاملا ایرانی بود.", 5),
            (users[2].id, sellers[1].id, "قیمت‌ها کمی بالاست ولی کیفیت خوبی داره.", 4),
            (users[3].id, sellers[2].id, "برگرش عالی بود، حتما دوباره سفارش میدم.", 5),
            (users[4].id, sellers[3].id, "باقلی پلوی فوق‌العاده‌ای بود، مزه خونگی داشت.", 5),
            (users[0].id, sellers[3].id, "قیمه نثارش خیلی خوب بود.", 4),
            (users[1].id, sellers[0].id, "معمولی بود، انتظارم بیشتر بود.", 3),
        ]
        for uid, sid, content, rating in comments_data:
            db.session.add(Comment(user_id=uid, seller_id=sid, content=content, rating=rating))

        db.session.commit()
        print("Database seeded successfully!")
        print("\n=== Login Credentials ===")
        print("Admin:     username=admin     password=admin123")
        print("Seller 1:  phone=09126666666  password=seller123  (پیتزا دانیال)")
        print("Seller 2:  phone=09127777777  password=seller123  (کباب سرای ریحون)")
        print("Seller 3:  phone=09128888888  password=seller123  (سوپر برگر)")
        print("Seller 4:  phone=09129999999  password=seller123  (رستوران سنتی نقش جهان)")
        print("Seller 5:  phone=09120000000  password=seller123  (چلوکبابی امیر)")
        print("User 1:    phone=09121111111  password=user123   (دانیال)")
        print("User 2:    phone=09122222222  password=user123   (سارا)")
        print("User 3:    phone=09123333333  password=user123   (محمد)")
        print("User 4:    phone=09124444444  password=user123   (زهرا)")
        print("User 5:    phone=09125555555  password=user123   (علی)")


if __name__ == "__main__":
    seed_data()
