from flask import Blueprint
from app.auth import login_required
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
            login_required(self.controller.profile)
        )
        
        self.bp.route("/logout", methods=["GET", "POST"])(
            login_required(self.controller.logout)
        )
        self.bp.route("/change-my-password", methods=["GET", "POST"], endpoint="change_my_password")(
            login_required(self.controller.change_my_password)
        )
        self.bp.route("/change_my_password", methods=["GET", "POST"], endpoint="change_my_password_underscore")(
            login_required(self.controller.change_my_password)
        )
        self.bp.route("/admin", methods=["GET", "POST"])(
            login_required(self.rolecontroller.admin)
        )
        self.bp.route("/teacher", methods=["GET", "POST"])(
            login_required(self.rolecontroller.teacher)
        )
        # Dashboard routes (simple frontends)
        self.bp.route("/student", methods=["GET", "POST"])(
            login_required(self.rolecontroller.student)
        )

        # Full workspaces (task pages) kept under separate paths
        self.bp.route("/teacher/tasks", methods=["GET", "POST"])(
            login_required(TaskController().teacher_dashboard)
        )
        self.bp.route("/student/tasks", methods=["GET", "POST"])(
            login_required(TaskController().student_dashboard)
        )

        return self.bp