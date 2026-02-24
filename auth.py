"""Auth: session-based login, role check (AppMfaReset, VpnMfaReset, OtpSet)."""
from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            return redirect(url_for("account.login", next=request.url))
        return f(*args, **kwargs)
    return wrapped

def role_required(role: str):
    """Require user to have this role (set at login from AD memberOf)."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not session.get("user"):
                return redirect(url_for("account.login", next=request.url))
            if role not in session.get("roles", []):
                return redirect(url_for("account.access_denied"))
            return f(*args, **kwargs)
        return wrapped
    return decorator
