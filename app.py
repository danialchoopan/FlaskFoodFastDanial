from flask import Flask
from models import db
from flask_cors import CORS
import os
from routes.auth_routes import auth_bp
from routes.user_api import user_api_bp
from routes.seller_api import seller_api_bp
from routes.web_user import web_user_bp
from routes.web_admin import admin_bp

def create_app():
    app = Flask(__name__)
    CORS(app)

    app.config['UPLOAD_FOLDER'] = 'static/upload'
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "danial-secret-key"

    db.init_app(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_api_bp)
    app.register_blueprint(seller_api_bp)
    app.register_blueprint(web_user_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
