from flask import Blueprint
from app.controllers.auth_controller import AuthController
from app.controllers.rolecontroller import RoleController
from app.controllers.task_controller import TaskController

class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()
        self.rolecontroller = RoleController()

    def register(self):
        self.bp.route("/", methods=["GET", "POST"])(
            self.controller.login
        )
        self.bp.route("/login", methods=["GET", "POST"])(
            self.controller.login
        )
        self.bp.route("/register", methods=["GET", "POST"])(
            self.controller.register
        )
        # username availability check for frontend
        self.bp.route("/check-username", methods=["GET"])(
            self.controller.check_username
        )
        self.bp.route("/forgot", methods=["GET", "POST"])(
            self.controller.forgot
        )
        self.bp.route("/verifyotp", methods=["GET", "POST"])(
            self.controller.verifyotp
        )
        
        # 👑 This is now the single, undisputed ruler of the /profile endpoint
        self.bp.route("/profile", methods=["GET", "POST"])(
            self.controller.profile
        )
        
        self.bp.route("/logout", methods=["GET", "POST"])(
            self.controller.logout
        )
        self.bp.route("/change-my-password", methods=["GET", "POST"])(
            self.controller.change_my_password
        )
        self.bp.route("/change_my_password", methods=["GET", "POST"])(
            self.controller.change_my_password
        )
        self.bp.route("/admin", methods=["GET", "POST"])(
            self.rolecontroller.admin
        )
        self.bp.route("/teacher", methods=["GET", "POST"])(
            self.rolecontroller.teacher
        )
        self.bp.route("/student", methods=["GET", "POST"])(
            self.rolecontroller.student
        )
        self.bp.route("/student/dashboard", methods=["GET"])(
            self.rolecontroller.student_dashboard
        )
        # Task detail page (view only)
        self.bp.route('/task/<int:task_id>', methods=['GET'])(
            TaskController().view_task
        )

        return self.bp