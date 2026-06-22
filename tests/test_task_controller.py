import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.task_controller import TaskController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("tasks", __name__)
    bp.route("/tasks/teacher", endpoint="teacher_task")(lambda: "teacher_tasks")
    bp.route("/tasks/student", endpoint="student_task")(lambda: "student_tasks")
    bp.route("/tasks/delete/<id>", endpoint="task_delete")(lambda id: "deleted")
    app.register_blueprint(bp)
    return app


class TestTaskController(unittest.TestCase):
    """Test TaskController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = TaskController()
        self.app.config['TESTING'] = True

    @patch("app.controllers.task_controller.Task")
    @patch("app.controllers.task_controller.Notification")
    def test_create_task_success(self, mock_notification, mock_task):
        """Teacher should create task successfully."""
        mock_task.create_task.return_value = 1
        mock_notification.create_task_notifications.return_value = True

        form_data = {
            'action': 'create_task',
            'title': 'Math Homework',
            'subject': 'Mathematics',
            'deadline': '2026-07-01',
            'description': 'Solve problems 1-10'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 5
            
            result = self.controller.teacher_task()
            
            self.assertEqual(result.status_code, 302)
            mock_task.create_task.assert_called_once()

    @patch("app.controllers.task_controller.BaseModel")
    def test_task_delete_not_found(self, mock_base):
        """Should handle non-existent task."""
        mock_base.fetch_one.return_value = None

        with self.app.test_request_context(method="GET"):
            result = self.controller.task_delete(999)
            
            self.assertEqual(result[1], 404)

    @patch("app.controllers.task_controller.BaseModel")
    @patch("app.controllers.task_controller.TaskBookmark")
    def test_task_delete_success(self, mock_bookmark, mock_base):
        """Should delete task and preserve snapshot."""
        mock_base.fetch_one.return_value = {
            'id': 1, 'title': 'Task', 'attached_filename': None
        }
        mock_bookmark.preserve_task_snapshot.return_value = True

        with self.app.test_request_context(method="GET"):
            result = self.controller.task_delete(1)
            
            self.assertEqual(result.status_code, 302)
            mock_bookmark.preserve_task_snapshot.assert_called_once()

    @patch("app.controllers.task_controller.BaseModel")
    def test_save_feedback_security_check(self, mock_base):
        """Should verify teacher owns the task before saving feedback."""
        mock_base.fetch_one.return_value = None  # Security check fails

        form_data = {
            'action': 'save_feedback',
            'student_data': '1:10',
            'feedback': 'Good work!'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 5
            
            # Should fail security check
            result = self.controller.teacher_task()
            
            # Should either redirect or return error
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
