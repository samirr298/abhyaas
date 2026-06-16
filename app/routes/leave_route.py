from flask import Blueprint
from app.auth import login_required
from app.controllers.leave_controller import LeaveController


class LeaveRoutes:
    def __init__(self):
        self.bp = Blueprint('leave', __name__)
        self.controller = LeaveController()

    def register(self):
        self.bp.route('/leave', methods=['GET', 'POST'])(
            self.controller.apply_leave
        )
        self.bp.route('/teacher/leave-requests', methods=['GET', 'POST'])(
            self.controller.teacher_leave_requests
        )
        return self.bp
