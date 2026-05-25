from flask import Blueprint
from app.controllers.attendance_controller import AttendanceController
from app.controllers.rolecontroller import RoleController
class AttendanceRoutes:
    def __init__(self):
        self.bp = Blueprint("attend", __name__)
        self.controller = AttendanceController()
        self.rolecontroller = RoleController()

    def register(self):
        self.bp.route("/attendance", methods=["GET", "POST"])(
            self.controller.mark_attendance
        )
        return self.bp