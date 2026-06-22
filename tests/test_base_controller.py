import unittest
from flask import Flask, session
from app.controllers.base_controller import BaseController


class TestBaseController(unittest.TestCase):
    """Test the BaseController helper methods."""
    
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test-secret"
        self.controller = BaseController()
        self.app.config['TESTING'] = True

    def test_validate_email_valid(self):
        """Should accept valid emails."""
        valid_emails = [
            'test@example.com',
            'user.name+tag@example.co.uk',
            'john_doe@domain.org'
        ]
        for email in valid_emails:
            self.assertTrue(self.controller._validate_email(email), 
                          f"Should accept {email}")

    def test_validate_email_invalid(self):
        """Should reject invalid emails."""
        invalid_emails = [
            'notanemail',
            '@example.com',
            'user@',
            'user @example.com',
            'user@.com'
        ]
        for email in invalid_emails:
            self.assertFalse(self.controller._validate_email(email),
                           f"Should reject {email}")

    def test_validate_name_valid(self):
        """Should accept names with 2+ characters."""
        self.assertTrue(self.controller._validate_name('Jo'))
        self.assertTrue(self.controller._validate_name('John Doe'))
        self.assertTrue(self.controller._validate_name('  Alice  '))

    def test_validate_name_invalid(self):
        """Should reject names with < 2 characters."""
        self.assertFalse(self.controller._validate_name('A'))
        self.assertFalse(self.controller._validate_name('  '))
        self.assertFalse(self.controller._validate_name(''))

    def test_validate_password_too_short(self):
        """Should reject passwords < 6 characters."""
        is_valid, message = self.controller._validate_password('12345')
        self.assertFalse(is_valid)
        self.assertIn('6 characters', message)

    def test_validate_password_valid(self):
        """Should accept passwords >= 6 characters."""
        is_valid, message = self.controller._validate_password('ValidPass123')
        self.assertTrue(is_valid)

    def test_session_property(self):
        """Should provide access to Flask session."""
        with self.app.test_request_context():
            session['test_key'] = 'test_value'
            self.assertEqual(self.controller.session.get('test_key'), 'test_value')


if __name__ == "__main__":
    unittest.main()
