from flask import Blueprint

from app.controllers.rolecontroller import RoleController


class RoleRoutes:
    def __init__(self):
        self.bp = Blueprint("role", __name__)
        self.controller = RoleController()

    def register(self):
        self.bp.route("/dashboard", methods=["GET"])(self.controller.dashboard)
        return self.bp