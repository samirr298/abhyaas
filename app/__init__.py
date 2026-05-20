from flask import Flask

from app.routes.auth_route import AuthRoutes
from datetime import timedelta
from app.database import Database

def create_app():
    app = Flask(__name__)
    # Secret key required for session/flash functionality. Replace in production.
    Database()
    app.secret_key = 'change-me-in-production'
    # keep session cookies persistent when requested (remember me)
    app.permanent_session_lifetime = timedelta(days=30)
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    return app