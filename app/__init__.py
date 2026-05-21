import os
from datetime import timedelta
# Added missing imports: request, abort, render_template
from flask import Flask, session, request, abort, render_template
import config
from .database import db,create_tables
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Initialize your database connection
    db()
    create_tables()
    # Session configurations
    app.permanent_session_lifetime = timedelta(days=30)
    app.secret_key = config.SECRET_KEY
    

    #configuring mail

    app.config.from_object(config)


    #initialising mail
    mail.init_app(app)
    # Register Blueprints
    from app.routes.auth_route import AuthRoutes
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())

    return app