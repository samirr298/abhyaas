from flask import render_template, session

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController
from app.models.announcement import Announcement


class RoleController:
    @login_required ##completed
    @role_required("admin")
    def admin(self):
        return render_template("users/admin_dashboard.html")

    @login_required
    @role_required("teacher")
    def teacher(self):
        return TaskController().teacher_dashboard()

    @login_required
    @role_required("student")
    def student(self):
        return TaskController().student_dashboard()

    @login_required
    @role_required("student")
    def student_dashboard(self):
        latest_announcements = Announcement.get_latest_announcements(3)
        return render_template(
            'users/student_dashboard.html',
            username=session.get('username'),
            latest_announcements=latest_announcements,
        )