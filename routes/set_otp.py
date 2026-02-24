"""Set OTP: same DB as Applications MFA. Lookup -> if registered confirm reset -> delete -> form (cell) -> insert REGISTRATIONS + JDG_MFA_OTP_USER_ADD_AUDIT."""
from flask import Blueprint, request, render_template, redirect, url_for, session

from config import get_upn_suffix
from services.ldap_service import find_user
from services.db_service import (
    is_registered,
    delete_registration,
    insert_audit,
    insert_registration_otp,
    insert_audit_otp_add,
)
from auth import login_required, role_required

set_otp = Blueprint("set_otp", __name__, url_prefix="/SetOtp")


def _mfa_id(sam: str) -> str:
    return sam if "@" in sam else f"{sam}@{get_upn_suffix()}"


@set_otp.route("/Reset", methods=["GET"])
@set_otp.route("/", methods=["GET"])
@login_required
@role_required("OtpSet")
def reset():
    return render_template("set_otp/reset.html")


@set_otp.route("/Lookup", methods=["POST"])
@login_required
@role_required("OtpSet")
def lookup():
    input_username = (request.form.get("InputUsername") or "").strip()
    if not input_username:
        return render_template("set_otp/reset.html", error="Username is required.")

    user_info = find_user(input_username)
    if not user_info:
        return render_template(
            "set_otp/reset.html",
            error="User not found in Active Directory.",
            input_username=input_username,
        )

    sam_account_name, display_name = user_info
    upn = _mfa_id(sam_account_name)
    is_reg = is_registered(upn)

    return render_template(
        "set_otp/confirm.html",
        input_username=input_username,
        sam_account_name=sam_account_name,
        display_name=display_name or sam_account_name,
        upn=upn,
        is_registered=is_reg,
    )


@set_otp.route("/Delete", methods=["POST"])
@login_required
@role_required("OtpSet")
def delete():
    sam_account_name = (request.form.get("SamAccountName") or "").strip()
    display_name = request.form.get("DisplayName") or ""
    if not sam_account_name:
        return "Invalid request.", 400

    upn = _mfa_id(sam_account_name)
    delete_registration(upn)
    logged_in_id = session.get("user") or "Unknown"
    insert_audit(logged_in_id, upn)

    session["set_otp_upn"] = upn
    session["set_otp_sam"] = sam_account_name
    session["set_otp_display_name"] = display_name
    return redirect(url_for("set_otp.form"))


@set_otp.route("/Form", methods=["GET"])
@login_required
@role_required("OtpSet")
def form():
    upn = session.get("set_otp_upn") or request.args.get("upn")
    sam = session.get("set_otp_sam") or request.args.get("sam", "")
    display_name = session.get("set_otp_display_name") or request.args.get("display_name", "")
    if not upn:
        return redirect(url_for("set_otp.reset"))
    return render_template(
        "set_otp/form.html",
        upn=upn,
        sam_account_name=sam,
        display_name=display_name,
        cell_value=request.args.get("cell", ""),
        error=request.args.get("error"),
    )


@set_otp.route("/Submit", methods=["POST"])
@login_required
@role_required("OtpSet")
def submit():
    upn = (request.form.get("UPN") or "").strip()
    cellfull = (request.form.get("CellNumber") or "").strip()
    sam_account_name = request.form.get("SamAccountName") or ""
    display_name = request.form.get("DisplayName") or ""

    if not upn:
        return redirect(url_for("set_otp.reset"))
    if not cellfull:
        return redirect(
            url_for(
                "set_otp.form",
                upn=upn,
                sam=sam_account_name,
                display_name=display_name,
                cell=request.form.get("CellNumber", ""),
                error="Cell number is required. Use country code format (e.g. +2782..., +2762...).",
            )
        )

    insert_registration_otp(upn, cellfull)
    logged_in_id = session.get("user") or "Unknown"
    insert_audit_otp_add(logged_in_id, upn)

    for key in ("set_otp_upn", "set_otp_sam", "set_otp_display_name"):
        session.pop(key, None)

    return render_template(
        "set_otp/success.html",
        sam_account_name=sam_account_name,
        display_name=display_name,
        upn=upn,
    )
