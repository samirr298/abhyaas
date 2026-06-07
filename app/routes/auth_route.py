from flask import Blueprint
from app.controllers.auth_controller import AuthController
from app.controllers.rolecontroller import RoleController

class AuthRoutes:
    def __init__(self):
        self.bp = Blueprint("auth", __name__)
        self.controller = AuthController()
        self.rolecontroller = RoleController()

    def register(self):
        self.bp.route("/", methods=["GET", "POST"]) (
            self.controller.login
        )
        self.bp.route("/login", methods=["GET", "POST"]) (
            self.controller.login
        )
        self.bp.route("/register", methods=["GET", "POST"]) (
            self.controller.register
        )
        # username availability check for frontend
        self.bp.route("/check-username", methods=["GET"]) (
            self.controller.check_username
        )
        self.bp.route("/forgot", methods=["GET", "POST"]) (
            self.controller.forgot
        )
        self.bp.route("/verifyotp", methods=["GET", "POST"]) (
            self.controller.verifyotp
        )
        
        # 👑 This is now the single, undisputed ruler of the /profile endpoint
        self.bp.route("/profile", methods=["GET", "POST"]) (
            self.controller.profile
        )
        
        self.bp.route("/logout", methods=["GET", "POST"]) (
            self.controller.logout
        )
        self.bp.route("/change-my-password", methods=["GET", "POST"]) (
            self.controller.change_my_password
        )
        self.bp.route("/change_my_password", methods=["GET", "POST"]) (
            self.controller.change_my_password
        )
        self.bp.route("/admin", methods=["GET", "POST"]) (
            self.rolecontroller.admin
        )
<<<<<<< HEAD
        self.bp.route("/teacher", methods=["GET", "POST"], endpoint="teacher_dashboard")(
            login_required(self.rolecontroller.teacher)
        )
        # Dashboard routes (simple frontends)
        self.bp.route("/student", methods=["GET", "POST"], endpoint="student_dashboard")(
            login_required(self.rolecontroller.student)
        )

        # Full workspaces (task pages) kept under separate paths
        self.bp.route("/teacher/tasks", methods=["GET", "POST"])(
            login_required(TaskController().teacher_task)
        )
        self.bp.route("/student/tasks", methods=["GET", "POST"])(
            login_required(TaskController().student_task)
        )
        self.bp.route("/task/<int:task_id>", methods=["GET", "POST"])(
            login_required(TaskController().task_detail)
        )
        self.bp.route("/delete-task/<int:task_id>", methods=["GET", "POST"])(
            login_required(TaskController().task_delete)
=======
        self.bp.route("/teacher", methods=["GET", "POST"]) (
            self.rolecontroller.teacher
        )
        self.bp.route("/student", methods=["GET", "POST"]) (
            self.rolecontroller.student
>>>>>>> feature/US-5.1-6.1-announcements-tasks-seasonbharat
        )

        return self.bp