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
            login_required(self.rolecontroller.admin_dashboard)
        )
        self.bp.route("/admin/fees", methods=["GET"])(
            self.rolecontroller.fees_management
        )
        self.bp.route("/teacher", methods=["GET", "POST"])(
            login_required(self.rolecontroller.teacher_dashboard)
        )
        # Dashboard routes (simple frontends)
        self.bp.route("/student", methods=["GET", "POST"], endpoint="student_dashboard")(
            login_required(self.rolecontroller.student_dashboard)
        )
        
    
        # Full workspaces (task pages) kept under separate paths
        

        return self.bp