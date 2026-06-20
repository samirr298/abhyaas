from datetime import datetime, date, timedelta
from flask import render_template, session, request, redirect, url_for, flash

from app.auth import login_required, role_required
from app.controllers.task_controller import TaskController
from app.models.base_model import BaseModel
from app.models.announcement import Announcement
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.task import Task, TaskBookmark
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
            action = request.form.get('action', 'update_role')

            if action == 'update_role':
                user_id = request.form.get('user_id')
                new_role = request.form.get('role')
                if user_id and new_role in ['student', 'teacher', 'admin']:
                    Users.update_role(user_id, new_role)
                    flash('Role updated successfully.', 'success')
                else:
                    flash('Invalid role assignment.', 'error')

            elif action == 'ban':
                user_id = request.form.get('user_id')
                if user_id:
                    target = Users.get_user_by_id(user_id)
                    if target and target['id'] != session.get('user_id'):
                        Users.ban_user(user_id)
                        flash(f"User '{target['name'] or target['username']}' has been banned.", "error")
                    else:
                        flash("You cannot ban yourself.", "error")

            elif action == 'unban':
                user_id = request.form.get('user_id')
                if user_id:
                    target = Users.get_user_by_id(user_id)
                    if target:
                        Users.unban_user(user_id)
                        flash(f"User '{target['name'] or target['username']}' has been unbanned.", "success")

            elif action == 'delete':
                user_id = request.form.get('user_id')
                if user_id:
                    target = Users.get_user_by_id(user_id)
                    if target:
                        if target['id'] == session.get('user_id'):
                            flash("You cannot delete your own account.", "error")
                            return redirect(url_for('auth.admin_dashboard'))
                        # Delete the user
                        Users.delete_user(user_id)
                        flash(f"User '{target['name'] or target['username']}' has been permanently deleted.", "success")

            elif action == 'add_user':
                # Admin-created user
                import re
                from werkzeug.security import generate_password_hash

                name = (request.form.get('name') or '').strip()
                username = (request.form.get('username') or '').strip()
                email = (request.form.get('email') or '').strip()
                role = (request.form.get('role') or '').strip().lower()
                password = request.form.get('password') or ''

                if not name or not username or not email or not role or not password:
                    flash('All fields are required to add a user.', 'error')
                    return redirect(url_for('auth.admin_dashboard'))

                if role not in ['student', 'teacher', 'admin']:
                    flash('Invalid role selection.', 'error')
                    return redirect(url_for('auth.admin_dashboard'))

                if not re.match(r'^[A-Za-z0-9_]{3,30}$', username):
                    flash('Username must be 3-30 chars and contain only letters, numbers, and underscores.', 'error')
                    return redirect(url_for('auth.admin_dashboard'))

                # Basic email sanity check
                if '@' not in email or '.' not in email:
                    flash('Please enter a valid email address.', 'error')
                    return redirect(url_for('auth.admin_dashboard'))

                password_hash = generate_password_hash(password)
                created = Users.create_user(name, username, email, password_hash, role)

                if created:
                    flash(f"User '{username}' added successfully.", 'success')
                else:
                    flash('Failed to add user. Username or email may already exist.', 'error')

            return redirect(url_for('auth.admin_dashboard'))


        users = Users.get_all_users()
        stats = Users.get_stats()
        return render_template("users/admin_dashboard.html", users=users, stats=stats)

    @login_required
    @role_required("admin")
    def fees_management(self):
        return render_template("users/fees_management.html")

    @login_required
    @role_required("teacher")
    def teacher_dashboard(self):
        teacher_tasks = Task.get_teacher_tasks(session.get('user_id')) or []
        latest_announcements = Announcement.get_latest_announcements(3)
        q = (request.args.get('q') or '').strip().lower()

        if q:
            teacher_tasks = [
                task for task in teacher_tasks
                if q in (task.get('title') or '').lower()
                or q in (task.get('subject') or '').lower()
                or q in (task.get('description') or '').lower()
            ]
            latest_announcements = [
                item for item in latest_announcements
                if q in (item.get('title') or '').lower()
                or q in (item.get('summary') or '').lower()
                or q in (item.get('category') or '').lower()
            ]

        submissions_sql = """
            SELECT
                s.id,
                s.task_id,
                s.student_id,
                s.status,
                s.submitted_at,
                s.submitted_filename,
                t.title AS task_title,
                u.name AS student_name
            FROM submissions s
            JOIN tasks t ON t.id = s.task_id
            JOIN users u ON u.id = s.student_id
            WHERE t.created_by = %s
            ORDER BY s.submitted_at DESC
        """
        recent_submissions = BaseModel.fetch_all(submissions_sql, [session.get('user_id')]) or []
        if q:
            recent_submissions = [
                item for item in recent_submissions
                if q in (item.get('task_title') or '').lower()
                or q in (item.get('student_name') or '').lower()
            ]

        today = date.today()
        record = Attendance.get_today_record(session.get('user_id'), today)
        attendance_status = record['status'].capitalize() if record else 'Not Marked'
        attendance_date_display = today.strftime('%A, %d %B %Y')

        attendance_start = today - timedelta(days=30)
        present_days = Attendance.get_status_count(session.get('user_id'), 'present', attendance_start, today + timedelta(days=1))
        absent_days = Attendance.get_status_count(session.get('user_id'), 'absent', attendance_start, today + timedelta(days=1))
        marked_days = present_days + absent_days
        attendance_rate = round((present_days / marked_days) * 100, 1) if marked_days else 0

        published_tasks_count = len(teacher_tasks)
        overdue_tasks_count = 0
        active_tasks_count = 0
        for task in teacher_tasks:
            due_value = task.get('due_date')
            if not due_value:
                continue
            due_date = due_value.date() if hasattr(due_value, 'date') else due_value
            if due_date < today:
                overdue_tasks_count += 1
            else:
                active_tasks_count += 1

        pending_reviews_count = sum(1 for item in recent_submissions if (item.get('status') or '') != 'Reviewed')
        reviewed_count = sum(1 for item in recent_submissions if (item.get('status') or '') == 'Reviewed')

        for task in teacher_tasks:
            completed_by_students = task.get('completed_by_students') or ''
            task['completed_count'] = len([value for value in completed_by_students.split(',') if value.strip()])

        return render_template(
            'users/teacher_dashboard.html',
            class_summary={},
            tasks=teacher_tasks[:3],
            feedback_queue=[],
            submissions=recent_submissions[:4],
            teacher_tasks=teacher_tasks,
            latest_announcements=latest_announcements,
            recent_submissions=recent_submissions,
            total_submissions=len(recent_submissions),
            published_tasks_count=published_tasks_count,
            active_tasks_count=active_tasks_count,
            overdue_tasks_count=overdue_tasks_count,
            pending_reviews_count=pending_reviews_count,
            reviewed_count=reviewed_count,
            attendance_rate=attendance_rate,
            username=session.get('username'),
            attendance_status=attendance_status,
            attendance_date_display=attendance_date_display,
            search_query=q,
            now=datetime.now(),
        )

  

    @login_required
    @role_required("student")
    def student_dashboard(self):
        latest_announcements = Announcement.get_latest_announcements(3)
        today_tasks = Task.get_today_tasks(session.get('user_id')) or []
        bookmarked_task_ids = TaskBookmark.get_bookmarked_task_ids(session.get('user_id'))
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
            bookmarked_task_ids=bookmarked_task_ids,
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
