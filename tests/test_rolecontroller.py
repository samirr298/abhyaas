import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.rolecontroller import RoleController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    bp.route("/admin", endpoint="admin_dashboard")(lambda: "admin")
    bp.route("/login", endpoint="login")(lambda: "login")
    app.register_blueprint(bp)
    return app


class TestRoleController(unittest.TestCase):
    """Test RoleController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = RoleController()
        self.app.config['TESTING'] = True
        self.auth_patch = patch("app.auth.Users.is_user_banned", return_value=False)
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    @patch("app.controllers.rolecontroller.render_template")
    def test_dashboard_renders(self, mock_render_template):
        """Dashboard should render for an authenticated user."""
        mock_render_template.return_value = "dashboard_page"

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            session['role'] = 'student'
            session['username'] = 'student1'

            result = self.controller.dashboard()

            self.assertEqual(result, "dashboard_page")
            mock_render_template.assert_called_once()

    @patch("app.controllers.rolecontroller.Users")
    @patch("app.controllers.rolecontroller.render_template")
    def test_admin_dashboard_update_role(self, mock_render_template, mock_users):
        """Admin should be able to update user roles."""
        mock_render_template.return_value = "admin_page"

        form_data = {
            'action': 'update_role',
            'user_id': '5',
            'role': 'teacher'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'admin'
            session['username'] = 'admin'
            
            result = self.controller.admin_dashboard()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Role updated successfully."), flashes)
            mock_users.update_role.assert_called_once_with('5', 'teacher')

    @patch("app.controllers.rolecontroller.Users")
    @patch("app.controllers.rolecontroller.render_template")
    def test_admin_dashboard_invalid_role(self, mock_render_template, mock_users):
        """Should reject invalid role assignments."""
        mock_render_template.return_value = "admin_page"

        form_data = {
            'action': 'update_role',
            'user_id': '5',
            'role': 'superuser'  # Invalid role
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'admin'
            session['username'] = 'admin'
            
            result = self.controller.admin_dashboard()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Invalid role assignment."), flashes)
            mock_users.update_role.assert_not_called()

    @patch("app.controllers.rolecontroller.Users")
    @patch("app.controllers.rolecontroller.render_template")
    def test_admin_ban_user(self, mock_render_template, mock_users):
        """Admin should be able to ban users."""
        mock_render_template.return_value = "admin_page"
        mock_users.get_user_by_id.return_value = {
            'id': 5, 'name': 'John Doe', 'username': 'johndoe'
        }

        form_data = {
            'action': 'ban',
            'user_id': '5'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'admin'
            
            result = self.controller.admin_dashboard()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('banned' in str(f[1]).lower() for f in flashes))
            mock_users.get_user_by_id.assert_called_once_with('5')
            mock_users.ban_user.assert_called_once_with('5')

    @patch("app.controllers.rolecontroller.Users")
    @patch("app.controllers.rolecontroller.render_template")
    def test_admin_cannot_ban_self(self, mock_render_template, mock_users):
        """Admin should not be able to ban themselves."""
        mock_render_template.return_value = "admin_page"
        mock_users.get_user_by_id.return_value = {
            'id': 1,
            'name': 'Admin User',
            'username': 'admin'
        }

        form_data = {
            'action': 'ban',
            'user_id': '1'  # Same as session user_id
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'admin'
            
            result = self.controller.admin_dashboard()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "You cannot ban yourself."), flashes)
            mock_users.ban_user.assert_not_called()

    @patch("app.controllers.rolecontroller.Users")
    @patch("app.controllers.rolecontroller.render_template")
    def test_admin_unban_user(self, mock_render_template, mock_users):
        """Admin should be able to unban users."""
        mock_render_template.return_value = "admin_page"

        form_data = {
            'action': 'unban',
            'user_id': '5'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'admin'
            
            result = self.controller.admin_dashboard()
            
            mock_users.get_user_by_id.assert_called_once_with('5')
            mock_users.unban_user.assert_called_once_with('5')

    @patch("app.controllers.rolecontroller.Task.get_teacher_tasks")
    @patch("app.controllers.rolecontroller.Announcement.get_latest_announcements")
    @patch("app.controllers.rolecontroller.BaseModel.fetch_all")
    @patch("app.controllers.rolecontroller.Attendance.get_today_record")
    @patch("app.controllers.rolecontroller.Attendance.get_status_count")
    @patch("app.controllers.rolecontroller.render_template")
    def test_teacher_dashboard_renders(self, mock_render, mock_status_count, mock_today_record, mock_fetch_all, mock_latest_announcements, mock_teacher_tasks):
        """Teacher dashboard should render with task and attendance data."""
        mock_render.return_value = "teacher_dashboard_page"
        mock_teacher_tasks.return_value = [
            {'id': 1, 'title': 'Task 1', 'subject': 'Math', 'description': 'Desc', 'due_date': None, 'completed_by_students': ''}
        ]
        mock_latest_announcements.return_value = [{'id': 1, 'title': 'Announcement', 'summary': 'Summary', 'category': 'Academic'}]
        mock_fetch_all.return_value = []
        mock_today_record.return_value = None
        mock_status_count.return_value = 0

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 5
            session['role'] = 'teacher'
            session['username'] = 'teacher1'

            result = self.controller.teacher_dashboard()

            self.assertEqual(result, "teacher_dashboard_page")
            mock_teacher_tasks.assert_called_once_with(5)

    @patch("app.controllers.rolecontroller.Task.get_today_tasks")
    @patch("app.controllers.rolecontroller.TaskBookmark.get_bookmarked_task_ids")
    @patch("app.controllers.rolecontroller.Notification.get_for_user")
    @patch("app.controllers.rolecontroller.Attendance.get_today_record")
    @patch("app.controllers.rolecontroller.Attendance.get_status_count")
    @patch("app.controllers.rolecontroller.Announcement.get_latest_announcements")
    @patch("app.controllers.rolecontroller.render_template")
    def test_student_dashboard_renders(self, mock_render, mock_latest_announcements, mock_status_count, mock_today_record, mock_notifications, mock_bookmarks, mock_today_tasks):
        """Student dashboard should render with task and notification data."""
        mock_render.return_value = "student_dashboard_page"
        mock_latest_announcements.return_value = [{'id': 1, 'title': 'Announcement'}]
        mock_today_tasks.return_value = [
            {'id': 1, 'title': 'Task 1', 'due_date': None, 'submission_status': 'Pending'}
        ]
        mock_bookmarks.return_value = [1]
        mock_notifications.return_value = []
        mock_today_record.return_value = None
        mock_status_count.return_value = 0

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 10
            session['role'] = 'student'
            session['username'] = 'student1'

            result = self.controller.student_dashboard()

            self.assertEqual(result, "student_dashboard_page")
            mock_today_tasks.assert_called_once_with(10)


if __name__ == "__main__":
    unittest.main()
