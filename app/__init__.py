import os
from datetime import timedelta
# Added missing imports: request, abort, render_template
from flask import Flask, session, request, abort, render_template
import config
from .database import Database
from flask_mail import Mail

mail = Mail()

def create_app():
    app = Flask(__name__)
    
    # Initialize your database connection
    Database.db()
    Database.create_users_table()
    Database.create_attendance_table()
    # Session configurations
    app.permanent_session_lifetime = timedelta(days=30)
    app.secret_key = config.SECRET_KEY
    

    #configuring mail

    app.config.from_object(config)


    #initialising mail
    mail.init_app(app)
    # Register Blueprints for auth
    from app.routes.auth_route import AuthRoutes
    auth_routes = AuthRoutes()
    app.register_blueprint(auth_routes.register())
    #register blueprints for attendance
    from app.routes.attendance_route import AttendanceRoutes
    attendance_routes = AttendanceRoutes()
    app.register_blueprint(attendance_routes.register())

    return app
