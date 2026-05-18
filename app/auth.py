

from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:
            flash("Please login first")
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

            if session["role"] != role:
                flash("Access denied")
                return redirect(url_for("auth.login"))

            return f(*args, **kwargs)

        return wrapper

    return decorator