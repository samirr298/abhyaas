import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from datetime import date, timedelta
from app.controllers.leave_controller import LeaveController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("leave", __name__)
    bp.route("/leave/apply", endpoint="apply_leave")(lambda: "apply")
    app.register_blueprint(bp)
    return app


class TestLeaveController(unittest.TestCase):
    """Test LeaveController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = LeaveController()
        self.app.config['TESTING'] = True
        self.auth_patch = patch("app.auth.Users.is_user_banned", return_value=False)
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    @patch("app.controllers.leave_controller.LeaveRequest")
    @patch.object(LeaveController, "render")
    def test_apply_leave_get_page(self, mock_render, mock_leave):
        """GET should show leave application form."""
        mock_render.return_value = "apply_leave_page"
        mock_leave.get_by_user.return_value = []
        mock_leave.get_unread_notifications_by_user.return_value = []

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            self.assertEqual(result, "apply_leave_page")
            mock_render.assert_called_once()

    @patch("app.controllers.leave_controller.LeaveRequest")
    def test_apply_leave_success(self, mock_leave):
        """Should submit leave request successfully."""
        mock_leave.create.return_value = True
        mock_leave.get_by_user.return_value = []
        mock_leave.get_unread_notifications_by_user.return_value = []

        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        next_day = (date.today() + timedelta(days=2)).isoformat()

        form_data = {
            'leave_date': tomorrow,
            'end_date': next_day,
            'leave_type': 'sick',
            'leave_reason': 'I am feeling unwell and need rest'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Leave request submitted successfully. Status is now Pending."), flashes)
            mock_leave.create.assert_called_once()

    @patch("app.controllers.leave_controller.LeaveRequest")
    def test_apply_leave_past_date_rejected(self, mock_leave):
        """Should reject leave requests with past dates."""
        past_date = (date.today() - timedelta(days=1)).isoformat()
        today = date.today().isoformat()

        form_data = {
            'leave_date': past_date,
            'end_date': today,
            'leave_type': 'sick',
            'leave_reason': 'I was sick yesterday'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('past' in str(f[1]).lower() for f in flashes))

    @patch("app.controllers.leave_controller.LeaveRequest")
    def test_apply_leave_end_before_start(self, mock_leave):
        """Should reject if end date is before start date."""
        day_after_tomorrow = (date.today() + timedelta(days=2)).isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        form_data = {
            'leave_date': day_after_tomorrow,
            'end_date': tomorrow,
            'leave_type': 'sick',
            'leave_reason': 'Testing validation'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('earlier' in str(f[1]).lower() for f in flashes))

    @patch("app.controllers.leave_controller.LeaveRequest")
    def test_apply_leave_short_reason(self, mock_leave):
        """Should reject reason shorter than 10 characters."""
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        form_data = {
            'leave_date': tomorrow,
            'end_date': tomorrow,
            'leave_type': 'sick',
            'leave_reason': 'Short'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('10 characters' in str(f[1]) for f in flashes))

    @patch("app.controllers.leave_controller.LeaveRequest")
    def test_apply_leave_cancel_pending(self, mock_leave):
        """Should cancel pending leave request."""
        mock_leave.delete_pending.return_value = True
        mock_leave.get_by_user.return_value = []
        mock_leave.get_unread_notifications_by_user.return_value = []

        form_data = {
            'action': 'cancel',
            'request_id': '1'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.apply_leave()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Pending leave request cancelled successfully."), flashes)
            mock_leave.delete_pending.assert_called_once_with(1, '1')


if __name__ == "__main__":
    unittest.main()
