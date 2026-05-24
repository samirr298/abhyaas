from flask import render_template, redirect, url_for, flash, session
import re


class BaseController:
    # Provides `render`, `redirect_to`, `flash` and `session` helpers so
    # child controllers stay concise.

    def render(self, template_name, **context):
        return render_template(template_name, **context)

    def redirect_to(self, endpoint, **values):
        return redirect(url_for(endpoint, **values))

    def flash(self, message, category='info'):
        flash(message, category)

    def _validate_email(self, email):
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None

    def _validate_name(self, name):
        return len(name.strip()) >= 2

    def _validate_password(self, password):
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"
        return True, "Password is valid"

    def _flash_errors(self, message):
        flash(message, 'error')

    @property
    def session(self):
        return session
