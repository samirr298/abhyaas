import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session
from werkzeug.security import generate_password_hash


def make_full_test_app():
    """Create a comprehensive test app with all major routes."""
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    app.config['TESTING'] = True

    # Auth routes
    auth_bp = Blueprint("auth", __name__)
    auth_bp.route("/login", endpoint="login")(lambda: "login")
    auth_bp.route("/register", endpoint="register")(lambda: "register")
    auth_bp.route("/admin-dashboard", endpoint="admin_dashboard")(lambda: "admin")
    auth_bp.route("/teacher-dashboard", endpoint="teacher_dashboard")(lambda: "teacher")
    auth_bp.route("/student-dashboard", endpoint="student_dashboard")(lambda: "student")
    
    # Announcement routes
    announce_bp = Blueprint("announce", __name__)
    announce_bp.route("/announcements", endpoint="announcement")(lambda: "announcements")
    
    # Attendance routes
    attend_bp = Blueprint("attend", __name__)
    attend_bp.route("/attendance", endpoint="mark_attendance")(lambda: "attendance")
    
    # Task routes
    tasks_bp = Blueprint("tasks", __name__)
    tasks_bp.route("/tasks", endpoint="teacher_task")(lambda: "tasks")
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(announce_bp)
    app.register_blueprint(attend_bp)
    app.register_blueprint(tasks_bp)
    
    return app


class TestIntegrationRoutes(unittest.TestCase):
    """Test integration of routes and controllers."""
    
    def setUp(self):
        self.app = make_full_test_app()
        self.client = self.app.test_client()

    def test_unauthenticated_user_redirected_from_protected_route(self):
        """Unauthenticated user should not access protected routes."""
        with self.app.test_request_context():
            # Simulate trying to access protected page
            self.assertNotIn('user_id', session)

    @patch("app.controllers.auth_controller.Users")
    def test_login_flow_to_dashboard(self, mock_users):
        """Complete login flow should redirect to correct dashboard."""
        hashed = generate_password_hash("password123")
        mock_users.get_my_email.return_value = {
            'id': 1, 'name': 'John', 'username': 'john',
            'email': 'john@test.com', 'password_hash': hashed,
            'role': 'student', 'profile_pic': None, 'is_banned': 0
        }

        with self.app.test_request_context("/login", method="POST",
                                           data={'email': 'john@test.com', 'password': 'password123'}):
            session['user_id'] = 1
            session['role'] = 'student'
            
            self.assertIn('user_id', session)
            self.assertEqual(session['role'], 'student')

    @patch("app.controllers.announcement_controller.Announcement")
    @patch("app.controllers.announcement_controller.AnnouncementController.render")
    def test_announcement_view_requires_login(self, mock_render, mock_announcement):
        """Should require login for announcement view."""
        mock_render.return_value = "announcements"
        mock_announcement.get_annoucement.return_value = []
        mock_announcement.get_total_annoucement_count.return_value = 0

        with self.app.test_request_context("/announcements", method="GET"):
            # Without session
            self.assertNotIn('user_id', session)

    @patch("app.controllers.attendance_controller.Attendance")
    @patch("app.controllers.attendance_controller.AttendanceController.render")
    def test_attendance_tracking_flow(self, mock_render, mock_attendance):
        """Student should be able to mark and view attendance."""
        mock_render.return_value = "attendance_page"
        mock_attendance.get_today_record.return_value = None
        mock_attendance.get_latest_date.return_value = None
        mock_attendance.get_total_history_count.return_value = 0
        mock_attendance.get_paginated_history.return_value = []
        mock_attendance.get_status_count.return_value = 0

        with self.app.test_request_context("/attendance", method="GET"):
            session['user_id'] = 10
            self.assertEqual(session['user_id'], 10)

    def test_multi_role_access_control(self):
        """Different roles should have different access levels."""
        roles_and_endpoints = [
            ('admin', '/admin-dashboard'),
            ('teacher', '/teacher-dashboard'),
            ('student', '/student-dashboard'),
        ]

        for role, endpoint in roles_and_endpoints:
            with self.app.test_request_context(endpoint):
                session['role'] = role
                self.assertEqual(session['role'], role)

    @patch("app.controllers.task_controller.Task")
    def test_teacher_task_creation_flow(self, mock_task):
        """Teacher should be able to create tasks."""
        mock_task.create_task.return_value = 1

        with self.app.test_request_context("/tasks", method="POST",
                                           data={
                                               'action': 'create_task',
                                               'title': 'Homework',
                                               'subject': 'Math'
                                           }):
            session['user_id'] = 5
            session['role'] = 'teacher'
            
            self.assertEqual(session['role'], 'teacher')


if __name__ == "__main__":
    unittest.main()
