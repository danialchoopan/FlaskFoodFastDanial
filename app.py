from flask import Flask
from models import db, Setting
from flask_cors import CORS
from flasgger import Swagger
import os
import json
from routes.auth_routes import auth_bp
from routes.user_api import user_api_bp
from routes.seller_api import seller_api_bp
from routes.web_user import web_user_bp
from routes.web_admin import admin_bp
from routes.web_seller import web_seller_bp
from routes.admin_api import admin_api_bp
from utils.csrf import generate_csrf_token

SWAGGER_TEMPLATE = {
    "openapi": "3.0.3",
    "info": {
        "title": "دانیال فست فود API",
        "description": "API Documentation for Danial Fast Food - Food ordering system with mobile app support and admin management.",
        "version": "1.0.0",
        "contact": {"name": "Danial"}
    },
    "servers": [{"url": "http://127.0.0.1:5000", "description": "Local Dev"}],
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "Authorization",
                "description": "Enter: Bearer {your_token}"
            }
        }
    },
    "tags": [
        {"name": "Auth", "description": "User & Seller registration and login"},
        {"name": "User API", "description": "Customer endpoints (token required)"},
        {"name": "Seller API", "description": "Restaurant endpoints (token required)"},
        {"name": "Admin API", "description": "Admin dashboard endpoints (session required)"},
    ]
}


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['UPLOAD_FOLDER'] = 'static/upload'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "danial-secret-key"
    app.config["SWAGGER"] = {
        "title": "دانیال فست فود API",
        "openapi": "3.0.3",
        "uiversion": 3,
    }

    db.init_app(app)
    Swagger(app, template=SWAGGER_TEMPLATE)

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_api_bp)
    app.register_blueprint(seller_api_bp)
    app.register_blueprint(web_user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(web_seller_bp)
    app.register_blueprint(admin_api_bp)

    app.jinja_env.globals['csrf_token'] = generate_csrf_token

    with app.app_context():
        db.create_all()
        _seed_default_settings()

    return app


def _seed_default_settings():
    defaults = {
        'food_categories': json.dumps(["پیتزا", "فست فود", "ایرانی", "سالاد", "دسر", "نوشیدنی"]),
        'cities': json.dumps(["تهران", "اصفهان", "شیراز", "تبریز", "مشهد"]),
        'platform_fee_percent': '5',
    }
    for key, value in defaults.items():
        if not Setting.query.filter_by(key=key).first():
            db.session.add(Setting(key=key, value=value))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
