from flask import Flask

from app.routes.auth_route import AuthRoutes


def create_app():
    app = Flask(__name__)
    # Secret key required for session/flash functionality. Replace in production.
    app.secret_key = 'change-me-in-production'
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    return app