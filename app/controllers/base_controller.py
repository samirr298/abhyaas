from flask import flash
import re


class BaseController:
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
