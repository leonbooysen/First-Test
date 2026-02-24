"""VPN MFA: reset (same flow as Applications MFA, uses MFADatabaseVPN). Login only."""
from flask import Blueprint, request, render_template, session

from config import get_upn_suffix
from services.ldap_service import find_user
from services.db_service import is_registered_vpn, delete_registration_vpn, insert_audit_vpn
from auth import login_required, role_required

vpn_mfa = Blueprint("vpn_mfa", __name__, url_prefix="/VpnMfa")

def _mfa_id(sam: str) -> str:
    return sam if "@" in sam else f"{sam}@{get_upn_suffix()}"

@vpn_mfa.route("/Reset", methods=["GET"])
@login_required
@role_required("VpnMfaReset")
def reset():
    return render_template("vpn_mfa/reset.html")

@vpn_mfa.route("/Lookup", methods=["POST"])
@login_required
@role_required("VpnMfaReset")
def lookup():
    input_username = (request.form.get("InputUsername") or "").strip()
    if not input_username:
        return render_template("vpn_mfa/reset.html", error="Username is required.")

    user_info = find_user(input_username)
    if not user_info:
        return render_template("vpn_mfa/reset.html", error="User not found in Active Directory.", input_username=input_username)

    sam_account_name, display_name = user_info
    mfa_id = _mfa_id(sam_account_name)
    is_reg = is_registered_vpn(mfa_id)

    return render_template(
        "vpn_mfa/confirm.html",
        input_username=input_username,
        sam_account_name=sam_account_name,
        display_name=display_name or sam_account_name,
        is_registered=is_reg,
    )

@vpn_mfa.route("/Delete", methods=["POST"])
@login_required
@role_required("VpnMfaReset")
def delete():
    sam_account_name = (request.form.get("SamAccountName") or "").strip()
    display_name = request.form.get("DisplayName") or ""
    if not sam_account_name:
        return "Invalid request.", 400

    mfa_id = _mfa_id(sam_account_name)
    delete_registration_vpn(mfa_id)
    logged_in_id = session.get("user") or "Unknown"
    insert_audit_vpn(logged_in_id, mfa_id)

    return render_template(
        "vpn_mfa/success.html",
        sam_account_name=sam_account_name,
        display_name=display_name,
    )
