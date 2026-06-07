from flask import render_template, session

from app.auth import login_required, role_required


class RoleController:
    @login_required
    def dashboard(self):
        return render_template(
            "users/role_dashboard.html",
            username=session.get("username"),
            role=session.get("role"),
        )

    @login_required
    @role_required("admin")
    def admin(self):
        return render_template("users/admin_dashboard.html")

    @login_required
    @role_required("teacher")
    def teacher(self):
        # Serve the static teacher task HTML (no backend logic)
        return render_template(
            'users/teacher_dashboard.html',
            class_summary={},
            tasks=[],
            feedback_queue=[],
            submissions=[],
            teacher_tasks=[],
            total_submissions=0,
            username=session.get('username'),
        )

    @login_required
    @role_required("student")
    def student(self):
        # Serve the static student task HTML (no backend logic)
        return render_template(
            'users/student_dashboard.html',
            overview={},
            tasks=[],
            feedback=[],
            today_tasks=[],
            username=session.get('username'),
        )