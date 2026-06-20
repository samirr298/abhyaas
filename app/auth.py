

from functools import wraps
from flask import session, redirect, url_for, flash
from app.models.user import Users


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first")
            return redirect(url_for("auth.login"))

        # Ban check — kick out banned users mid-session
        if Users.is_user_banned(session["user_id"]):
            session.clear()
            flash("Your account has been banned. Contact an administrator.", "error")
            return redirect(url_for("auth.login"))

        return f(*args, **kwargs)

    return wrapper


def role_required(role):

    def decorator(f):

        @wraps(f)
        def wrapper(*args, **kwargs):

            if "role" not in session:
                flash("Unauthorized access")
                return redirect(url_for("auth.login"))

            if session["role"] != role and session["role"] != 'admin':
                flash("Access denied")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)

        return wrapper

    return decorator
