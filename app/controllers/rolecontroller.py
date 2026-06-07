from flask import render_template, session, request, redirect, url_for, flash

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController
from app.models.announcement import Announcement
from app.models.user import Users


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
    def admin_dashboard(self):
        if request.method == 'POST':
            user_id = request.form.get('user_id')
            new_role = request.form.get('role')
            if user_id and new_role in ['student', 'teacher', 'admin']:
                Users.update_role(user_id, new_role)
                flash('Role updated successfully.', 'success')
            else:
                flash('Invalid role assignment.', 'error')
            return redirect(url_for('auth.admin_dashboard'))

        users = Users.get_all_users()
        return render_template("users/admin_dashboard.html", users=users)

    @login_required
    @role_required("admin")
    def fees_management(self):
        return render_template("users/fees_management.html")

    @login_required
    @role_required("teacher")
    def teacher_dashboard(self):
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
    def student_dashboard(self):
        latest_announcements = Announcement.get_latest_announcements(3)
        return render_template(
            'users/student_dashboard.html',
            username=session.get('username'),
            latest_announcements=latest_announcements,
            overview={},
            tasks=[],
            feedback=[],
            today_tasks=[],
        )