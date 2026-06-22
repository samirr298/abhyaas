import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, session
from app.controllers.quiz_controller import QuizController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    app.add_url_rule('/login', endpoint='login', view_func=lambda: 'login')
    return app


class TestQuizController(unittest.TestCase):
    """Test QuizController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = QuizController()
        self.app.config['TESTING'] = True

    @patch("app.controllers.quiz_controller.render_template")
    def test_quiz_generator_page_get(self, mock_render):
        """Should display quiz generator page."""
        mock_render.return_value = "quiz_generator_page"
        
        result = self.controller.quiz_generator_page()
        
        self.assertEqual(result, "quiz_generator_page")
        mock_render.assert_called_once_with('quiz/quiz_generator.html', quiz_data=None)

    @patch("app.controllers.quiz_controller.render_template")
    def test_quiz_history_page_no_login(self, mock_render):
        """Should redirect if user not logged in."""
        with self.app.test_request_context(method="GET"):
            result = self.controller.quiz_history_page()
            
            self.assertEqual(result.status_code, 302)
            self.assertIn('/login', result.location)

    @patch("app.controllers.quiz_controller.render_template")
    def test_quiz_history_page_with_login(self, mock_render):
        """Should display history page for logged in user."""
        mock_render.return_value = "quiz_history_page"
        
        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            
            result = self.controller.quiz_history_page()
            
            self.assertEqual(result, "quiz_history_page")

    @patch("app.controllers.quiz_controller.render_template")
    def test_start_quiz_session_basic(self, mock_render):
        """Should initialize quiz session with basic config."""
        mock_render.return_value = "quiz_interactive_page"
        
        form_data = {
            'source_text': 'This is a test passage.',
            'num_questions': '5',
            'enable_timer': 'false'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.start_quiz_session()
            
            self.assertEqual(result, "quiz_interactive_page")
            self.assertEqual(session['quiz_state']['total_questions'], 5)
            self.assertIsNone(session['quiz_state']['time_limit_per_question'])

    @patch("app.controllers.quiz_controller.render_template")
    def test_start_quiz_session_with_timer(self, mock_render):
        """Should initialize quiz with timer."""
        mock_render.return_value = "quiz_interactive_page"
        
        form_data = {
            'source_text': 'Test passage.',
            'num_questions': '3',
            'enable_timer': 'true',
            'timer_min': '2',
            'timer_sec': '30'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.start_quiz_session()
            
            # 2 minutes 30 seconds = 150 seconds
            self.assertEqual(session['quiz_state']['time_limit_per_question'], 150)

    @patch("app.controllers.quiz_controller.render_template")
    def test_start_quiz_session_timer_boundaries(self, mock_render):
        """Should enforce timer boundaries (30s-5min)."""
        mock_render.return_value = "quiz_interactive_page"
        
        # Test min boundary (too low)
        form_data = {
            'source_text': 'Test.',
            'num_questions': '1',
            'enable_timer': 'true',
            'timer_min': '0',
            'timer_sec': '10'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            self.controller.start_quiz_session()
            
            # Should enforce 30 second minimum
            self.assertEqual(session['quiz_state']['time_limit_per_question'], 30)


if __name__ == "__main__":
    unittest.main()
