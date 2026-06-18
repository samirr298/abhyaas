from datetime import datetime, date, timedelta
from flask import render_template, session, request, redirect, url_for, flash

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController
from app.models.announcement import Announcement
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.task import Task
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
        teacher_tasks = Task.get_teacher_tasks(session.get('user_id')) or []
        today = date.today()
        record = Attendance.get_today_record(session.get('user_id'), today)
        attendance_status = record['status'].capitalize() if record else 'Not Marked'
        attendance_date_display = today.strftime('%A, %d %B %Y')

        return render_template(
            'users/teacher_dashboard.html',
            class_summary={},
            tasks=[],
            feedback_queue=[],
            submissions=[],
            teacher_tasks=teacher_tasks,
            total_submissions=len(teacher_tasks),
            username=session.get('username'),
            attendance_status=attendance_status,
            attendance_date_display=attendance_date_display,
        )

  

    @login_required
    @role_required("student")
    def student_dashboard(self):
        latest_announcements = Announcement.get_latest_announcements(3)
        today_tasks = Task.get_today_tasks(session.get('user_id')) or []
        pending_tasks = [task for task in today_tasks if (task.get('submission_status') or '') != 'Reviewed']
        notifications = Notification.get_for_user(session.get('user_id')) or []
        deadline_reminders = [item for item in notifications if item.get('notification_type') == 'deadline_reminder']
        today = date.today()
        record = Attendance.get_today_record(session.get('user_id'), today)
        attendance_status = record['status'].capitalize() if record else 'Not Marked'
        attendance_date_display = today.strftime('%A, %d %B %Y')

        total_tasks_count = len(today_tasks)
        completed_count = sum(1 for task in today_tasks if (task.get('submission_status') or '') == 'Reviewed')
        upcoming_deadlines = 0
        for task in today_tasks:
            due_value = task.get('due_date')
            if not due_value:
                continue
            due_date = due_value.date() if hasattr(due_value, 'date') else due_value
            if due_date >= today:
                upcoming_deadlines += 1

        attendance_start = today - timedelta(days=30)
        present_days = Attendance.get_status_count(session.get('user_id'), 'present', attendance_start, today + timedelta(days=1))
        absent_days = Attendance.get_status_count(session.get('user_id'), 'absent', attendance_start, today + timedelta(days=1))
        marked_days = present_days + absent_days
        attendance_rate = round((present_days / marked_days) * 100, 1) if marked_days else 0

        return render_template(
            'users/student_dashboard.html',
            username=session.get('username'),
            latest_announcements=latest_announcements,
            overview={},
            tasks=[],
            feedback=[],
            today_tasks=today_tasks,
            pending_tasks=pending_tasks,
            deadline_reminders=deadline_reminders,
            attendance_status=attendance_status,
            attendance_date_display=attendance_date_display,
            attendance_rate=attendance_rate,
            total_tasks_count=total_tasks_count,
            completed_count=completed_count,
            pending_count=len(pending_tasks),
            upcoming_deadlines=upcoming_deadlines,
            now=datetime.now(),
        )