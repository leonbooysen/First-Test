"""MFA Reset Portal - Flask app (Python 3)."""
import logging
import os
from datetime import datetime
from flask import Flask

from config import load_config
from routes.account import account as account_bp
from routes.home import home as home_bp
from routes.applications_mfa import applications_mfa as applications_mfa_bp
from routes.vpn_mfa import vpn_mfa as vpn_mfa_bp
from routes.set_otp import set_otp as set_otp_bp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    load_config()
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
    app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 8  # 8 hours

    @app.context_processor
    def inject_year():
        return {"year": datetime.now().year}

    app.register_blueprint(account_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(applications_mfa_bp)
    app.register_blueprint(vpn_mfa_bp)
    app.register_blueprint(set_otp_bp)

    @app.route("/Home/Error")
    def error():
        return "An error occurred.", 500

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
