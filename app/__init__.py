from flask import Flask
from datetime import timedelta
import os
from dotenv import load_dotenv

def create_app():

    app = Flask(__name__)

    load_dotenv()

    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY")

    app.config["RAZORPAY_KEY_ID"] = os.getenv("RAZORPAY_KEY_ID")

    app.config["RAZORPAY_KEY_SECRET"] = os.getenv("RAZORPAY_KEY_SECRET")

    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

    from app.routes.home import home_bp
    from app.routes.auth import auth_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(auth_bp)

    return app