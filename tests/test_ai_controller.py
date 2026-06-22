import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint
from app.controllers.ai_controller import AIController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"
    return app


class TestAIController(unittest.TestCase):
    """Test AIController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.app.config['TESTING'] = True

    @patch("app.controllers.ai_controller.os.getenv")
    @patch("app.controllers.ai_controller.genai.Client")
    def test_ai_controller_initialization(self, mock_client, mock_getenv):
        """Should initialize with API key."""
        mock_getenv.return_value = "test-api-key"
        
        controller = AIController()
        
        self.assertIsNotNone(controller.client)

    @patch("app.controllers.ai_controller.AIController.__init__", lambda x: None)
    def test_is_heavy_task_detection(self):
        """Should detect heavy tasks and reject them."""
        controller = AIController()
        controller.HEAVY_TASK_PATTERNS = [
            "full code", "implement", "build a complete", 
            "debug entire", "refactor"
        ]
        
        heavy_tasks = [
            "implement a full code solution",
            "build a complete project for me",
            "debug entire codebase",
            "refactor this application"
        ]
        
        for task in heavy_tasks:
            self.assertTrue(controller._is_heavy_task(task),
                          f"Should detect '{task}' as heavy")

    @patch("app.controllers.ai_controller.AIController.__init__", lambda x: None)
    def test_is_heavy_task_allows_light(self):
        """Should allow light tasks."""
        controller = AIController()
        controller.HEAVY_TASK_PATTERNS = ["full code", "implement"]
        
        light_tasks = [
            "What is Python?",
            "How do I sort a list?",
            "Explain REST API"
        ]
        
        for task in light_tasks:
            self.assertFalse(controller._is_heavy_task(task),
                           f"Should allow '{task}'")

    @patch("app.controllers.ai_controller.os.getenv")
    @patch("app.controllers.ai_controller.genai.Client")
    def test_ask_heavy_task_rejection(self, mock_client_class, mock_getenv):
        """Should reject heavy tasks."""
        mock_getenv.return_value = "test-key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        controller = AIController()

        with self.app.test_request_context(method="POST", 
                                          data={'question': 'implement a full code system'}):
            result, status = controller.ask()
            
            self.assertEqual(status, 200)
            self.assertIn("help with heavy tasks", result.lower())

    @patch("app.controllers.ai_controller.os.getenv")
    @patch("app.controllers.ai_controller.genai.Client")
    def test_ask_empty_question(self, mock_client_class, mock_getenv):
        """Should reject empty questions."""
        mock_getenv.return_value = "test-key"
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        controller = AIController()

        with self.app.test_request_context(method="POST", 
                                          data={'question': '   '}):
            result, status = controller.ask()
            
            self.assertEqual(status, 400)
            self.assertIn("type a question", result.lower())

    @patch("app.controllers.ai_controller.os.getenv")
    @patch("app.controllers.ai_controller.genai.Client")
    def test_ask_successful_light_question(self, mock_client_class, mock_getenv):
        """Should answer light questions successfully."""
        mock_getenv.return_value = "test-key"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Python is a programming language."
        mock_client.models.generate_content.return_value = mock_response
        mock_client_class.return_value = mock_client
        
        controller = AIController()

        with self.app.test_request_context(method="POST", 
                                          data={'question': 'What is Python?'}):
            result, status = controller.ask()
            
            self.assertEqual(status, 200)
            self.assertIn("Python", result)


if __name__ == "__main__":
    unittest.main()
