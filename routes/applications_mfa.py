"""Applications MFA: reset (lookup -> confirm -> delete -> success)."""
from flask import Blueprint, request, render_template, redirect, url_for, session

from config import get_upn_suffix
from services.ldap_service import find_user
from services.db_service import is_registered, delete_registration, insert_audit
from auth import login_required, role_required

applications_mfa = Blueprint("applications_mfa", __name__, url_prefix="/ApplicationsMfa")

def _mfa_id(sam: str) -> str:
    return sam if "@" in sam else f"{sam}@{get_upn_suffix()}"

@applications_mfa.route("/Reset", methods=["GET"])
@login_required
@role_required("AppMfaReset")
def reset():
    return render_template("applications_mfa/reset.html")

@applications_mfa.route("/Lookup", methods=["POST"])
@login_required
@role_required("AppMfaReset")
def lookup():
    input_username = (request.form.get("InputUsername") or "").strip()
    if not input_username:
        return render_template("applications_mfa/reset.html", error="Username is required.")

    user_info = find_user(input_username)
    if not user_info:
        return render_template("applications_mfa/reset.html", error="User not found in Active Directory.", input_username=input_username)

    sam_account_name, display_name = user_info
    mfa_id = _mfa_id(sam_account_name)
    is_reg = is_registered(mfa_id)

    return render_template(
        "applications_mfa/confirm.html",
        input_username=input_username,
        sam_account_name=sam_account_name,
        display_name=display_name or sam_account_name,
        is_registered=is_reg,
    )

@applications_mfa.route("/Delete", methods=["POST"])
@login_required
@role_required("AppMfaReset")
def delete():
    sam_account_name = (request.form.get("SamAccountName") or "").strip()
    display_name = request.form.get("DisplayName") or ""
    if not sam_account_name:
        return "Invalid request.", 400

    mfa_id = _mfa_id(sam_account_name)
    delete_registration(mfa_id)
    logged_in_id = session.get("user") or "Unknown"
    insert_audit(logged_in_id, mfa_id)

    return render_template(
        "applications_mfa/success.html",
        sam_account_name=sam_account_name,
        display_name=display_name,
    )
