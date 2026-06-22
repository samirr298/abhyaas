import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from datetime import date, timedelta
from app.controllers.attendance_controller import AttendanceController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("attend", __name__)
    bp.route("/attendance", endpoint="mark_attendance")(lambda: "attendance")
    bp.route("/manage-attendance", endpoint="manage_attendance")(lambda: "manage")
    app.register_blueprint(bp)
    return app


class TestAttendanceController(unittest.TestCase):
    """Test AttendanceController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = AttendanceController()
        self.app.config['TESTING'] = True

    @patch("app.controllers.attendance_controller.Attendance")
    @patch.object(AttendanceController, "render")
    def test_mark_attendance_get_request(self, mock_render, mock_attendance):
        """GET request should show attendance page with stats."""
        mock_render.return_value = "attendance_page"
        mock_attendance.get_today_record.return_value = {'status': 'present'}
        mock_attendance.get_latest_date.return_value = date.today() - timedelta(days=1)
        mock_attendance.get_total_history_count.return_value = 20
        mock_attendance.get_paginated_history.return_value = []
        mock_attendance.get_status_count.side_effect = lambda u, s, *args: 18 if s == 'present' else 2

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            
            result = self.controller.mark_attendance()
            
            self.assertEqual(result, "attendance_page")
            # Verify render was called
            self.assertTrue(mock_render.called)

    @patch("app.controllers.attendance_controller.Attendance")
    def test_mark_attendance_post_success(self, mock_attendance):
        """POST should mark attendance and show success."""
        today = date.today()
        mock_attendance.get_today_record.return_value = None  # No existing record
        mock_attendance.mark_present.return_value = True

        with self.app.test_request_context(method="POST"):
            session['user_id'] = 1
            
            result = self.controller.mark_attendance()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Attendance marked successfully!"), flashes)

    @patch("app.controllers.attendance_controller.Attendance")
    def test_mark_attendance_already_marked(self, mock_attendance):
        """Should prevent duplicate attendance for same day."""
        today = date.today()
        mock_attendance.get_today_record.return_value = {'status': 'present', 'marked_at': today}

        with self.app.test_request_context(method="POST"):
            session['user_id'] = 1
            
            result = self.controller.mark_attendance()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("warning", "Attendance already updated for today."), flashes)

    @patch("app.controllers.attendance_controller.Attendance")
    @patch.object(AttendanceController, "render")
    def test_attendance_percentage_calculation(self, mock_render, mock_attendance):
        """Should correctly calculate attendance percentage."""
        mock_render.return_value = "attendance_page"
        mock_attendance.get_today_record.return_value = None
        mock_attendance.get_latest_date.return_value = None
        mock_attendance.get_total_history_count.return_value = 20
        mock_attendance.get_paginated_history.return_value = []
        # 18 present, 2 absent = 90%
        mock_attendance.get_status_count.side_effect = lambda u, s, *args: 18 if s == 'present' else 2

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            
            result = self.controller.mark_attendance()
            
            # Check render was called with correct percentage
            call_args = mock_render.call_args[1]
            self.assertEqual(call_args['current_rate'], 90.0)


if __name__ == "__main__":
    unittest.main()
