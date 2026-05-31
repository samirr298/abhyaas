from flask import render_template, session

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController


class RoleController:
    @login_required
    @role_required("admin")
    def admin(self):
        return render_template("users/admin_dashboard.html")

    @login_required
    @role_required("teacher")
    def teacher(self):
        # render the simple teacher dashboard (no JS)
        return render_template(
            'users/teacher_dashboard.html',
            username=session.get('username'),
            class_summary=None,
            tasks=None,
        )

    @login_required
    @role_required("student")
    def student(self):
        # render the simple student dashboard (no JS)
        return render_template(
            'users/student_dashboard.html',
            username=session.get('username'),
            overview=None,
            tasks=None,
        )