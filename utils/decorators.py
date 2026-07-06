from functools import wraps
from flask import session, redirect, url_for


def admin_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


def seller_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("seller_id"):
            return redirect(url_for("web_seller.login"))
        return f(*args, **kwargs)
    return decorated
