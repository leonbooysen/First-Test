"""MFA Reset Portal - Flask app (Python 3)."""
import logging
import os
from datetime import datetime
from flask import Flask, jsonify

from config import load_config
from routes.account import account as account_bp
from routes.home import home as home_bp
from routes.applications_mfa import applications_mfa as applications_mfa_bp
from routes.vpn_mfa import vpn_mfa as vpn_mfa_bp
from routes.set_otp import set_otp as set_otp_bp

# Production: require FLASK_SECRET_KEY (set in Fargate task def / env)
_IS_PRODUCTION = os.environ.get("FLASK_ENV", "").strip().lower() == "production"
if _IS_PRODUCTION and not os.environ.get("FLASK_SECRET_KEY", "").strip():
    raise RuntimeError("FLASK_SECRET_KEY must be set in production (e.g. via Fargate task env)")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)


def create_app():
    load_config()
    app = Flask(__name__)
    app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "change-me-in-production"
    app.config["PERMANENT_SESSION_LIFETIME"] = 60 * 60 * 8  # 8 hours

    @app.context_processor
    def inject_year():
        return {"year": datetime.now().year}

    app.register_blueprint(account_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(applications_mfa_bp)
    app.register_blueprint(vpn_mfa_bp)
    app.register_blueprint(set_otp_bp)

    # Health check for ALB / Fargate (no auth)
    @app.route("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    @app.route("/Home/Error")
    def error():
        return "An error occurred.", 500

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1" and not _IS_PRODUCTION
    app.run(host="0.0.0.0", port=port, debug=debug)
