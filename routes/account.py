"""Account: login (AD), logout, access_denied."""
import logging
from flask import Blueprint, request, redirect, url_for, render_template, session

from config import get_ad_groups
from services.ldap_service import validate_credentials_and_get_member_of, is_in_member_of
from auth import login_required

logger = logging.getLogger(__name__)

account = Blueprint("account", __name__, url_prefix="/Account")

@account.route("/Login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user"):
            return redirect(request.args.get("next") or url_for("home.index"))
        return render_template("account/login.html", return_url=request.args.get("next"))

    # POST
    username = (request.form.get("Username") or "").strip()
    password = request.form.get("Password") or ""
    return_url = request.form.get("ReturnUrl") or request.args.get("next") or "/"

    if not username:
        return render_template("account/login.html", error="Username is required.", return_url=return_url)
    if not password:
        return render_template("account/login.html", error="Password is required.", return_url=return_url, username=username)

    valid, member_of_dns = validate_credentials_and_get_member_of(username, password)
    if not valid or member_of_dns is None:
        logger.warning("Login failed invalid credentials user=%s", username)
        return render_template("account/login.html", error="Invalid username or password.", return_url=return_url, username=username)

    logger.info("Login successful user=%s memberOf_count=%s", username, len(member_of_dns) if member_of_dns else 0)
    groups = get_ad_groups()
    roles = []
    if groups.get("AppMfaReset") and is_in_member_of(member_of_dns, groups["AppMfaReset"]):
        roles.append("AppMfaReset")
    if groups.get("VpnMfaReset") and is_in_member_of(member_of_dns, groups["VpnMfaReset"]):
        roles.append("VpnMfaReset")
    if groups.get("OtpSet") and is_in_member_of(member_of_dns, groups["OtpSet"]):
        roles.append("OtpSet")
    logger.info("Login roles user=%s roles=%s", username, roles)

    session["user"] = username
    session["roles"] = roles
    session.permanent = True
    return redirect(return_url)

@account.route("/Logout", methods=["POST"])
@login_required
def logout():
    logger.info("Logout user=%s", session.get("user"))
    session.clear()
    return redirect(request.form.get("return_url") or request.args.get("return_url") or "/")

@account.route("/AccessDenied")
def access_denied():
    logger.warning("Access denied user=%s", session.get("user"))
    return render_template("account/access_denied.html")
