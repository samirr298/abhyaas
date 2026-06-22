import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session
from app.controllers.message_controller import ChatController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("chat", __name__)
    bp.route("/messages", endpoint="message_center")(lambda: "messages")
    bp.route("/login", endpoint="login")(lambda: "login")
    app.register_blueprint(bp)

    auth_bp = Blueprint("auth", __name__)
    auth_bp.route("/login", endpoint="login")(lambda: "login")
    app.register_blueprint(auth_bp)
    return app


class TestChatController(unittest.TestCase):
    """Test ChatController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = ChatController()
        self.app.config['TESTING'] = True

    @patch("app.controllers.message_controller.BaseModel")
    @patch.object(ChatController, "render")
    def test_message_center_teacher_view(self, mock_render, mock_base):
        """Teacher should see list of student conversations."""
        mock_render.return_value = "messages_page"
        mock_base.fetch_all.return_value = [
            {'conversation_id': 1, 'user_id': 10, 'name': 'Student1', 
             'last_message': 'Hello', 'last_message_time': '10:30 AM'},
            {'conversation_id': 2, 'user_id': 11, 'name': 'Student2', 
             'last_message': 'Thanks', 'last_message_time': '09:15 AM'}
        ]

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 5
            session['role'] = 'teacher'
            
            result = self.controller.message_center()
            
            self.assertEqual(result, "messages_page")
            # Verify it fetched contacts
            self.assertTrue(mock_base.fetch_all.called)

    @patch("app.controllers.message_controller.BaseModel")
    @patch.object(ChatController, "render")
    def test_message_center_student_view(self, mock_render, mock_base):
        """Student should see list of teacher conversations."""
        mock_render.return_value = "messages_page"
        mock_base.fetch_all.side_effect = [
            # First call - teachers list
            [{'conversation_id': 1, 'user_id': 5, 'name': 'TeacherA', 
              'last_message': 'Assignment due', 'last_message_time': '02:00 PM'}],
            # Second call - message history (empty for new conversation)
            []
        ]

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 10
            session['role'] = 'student'
            
            result = self.controller.message_center()
            
            self.assertEqual(result, "messages_page")

    @patch("app.controllers.message_controller.BaseModel")
    @patch.object(ChatController, "render")
    def test_message_center_with_conversation(self, mock_render, mock_base):
        """Should fetch message history for active conversation."""
        mock_render.return_value = "messages_page"
        mock_base.fetch_all.side_effect = [
            # Sidebar contacts
            [{'conversation_id': 1, 'user_id': 5, 'name': 'TeacherA'}],
            # Message history
            [{'sender_id': 5, 'message_text': 'Hello student', 'msg_time': '10:00 AM'},
             {'sender_id': 10, 'message_text': 'Hi teacher', 'msg_time': '10:05 AM'}]
        ]
        mock_base.fetch_one.return_value = {
            'teacher_name': 'TeacherA', 'student_name': 'StudentB'
        }

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 10
            session['role'] = 'student'
            
            result = self.controller.message_center(active_conv_id=1)
            
            self.assertEqual(result, "messages_page")
            # Verify it called to get message history
            self.assertEqual(mock_base.fetch_all.call_count, 2)

    def test_message_center_requires_login(self):
        """Should redirect to login if not authenticated."""
        with self.app.test_request_context(method="GET"):
            # No session data
            result = self.controller.message_center()
            
            self.assertEqual(result.status_code, 302)
            self.assertIn('login', result.location)


if __name__ == "__main__":
    unittest.main()
