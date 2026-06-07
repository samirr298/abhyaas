from flask import Blueprint
from app.auth import login_required
from app.controllers.attendance_controller import AttendanceController
from app.controllers.rolecontroller import RoleController

class AttendanceRoutes:
    def __init__(self):
        self.bp = Blueprint("attend", __name__)
        self.controller = AttendanceController()
        self.rolecontroller = RoleController()

    def register(self):
        self.bp.route("/attendance", methods=["GET", "POST"])(
            login_required(self.controller.mark_attendance)
        )
        self.bp.route("/attendance/manage", methods=["GET", "POST"])(
            self.controller.manage_attendance
        )
        return self.bp