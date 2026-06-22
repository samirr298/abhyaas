import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from werkzeug.security import generate_password_hash
from app.controllers.auth_controller import AuthController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/login", endpoint="login")(lambda: "login")
    bp.route("/register", endpoint="register")(lambda: "register")
    bp.route("/admin-dashboard", endpoint="admin_dashboard")(lambda: "admin")
    bp.route("/teacher-dashboard", endpoint="teacher_dashboard")(lambda: "teacher")
    bp.route("/student-dashboard", endpoint="student_dashboard")(lambda: "student")
    bp.route("/forgot", endpoint="forgot")(lambda: "forgot")
    bp.route("/verify-otp", endpoint="verifyotp")(lambda: "verify")
    app.register_blueprint(bp)
    return app


class TestAuthControllerLogin(unittest.TestCase):
    """Test AuthController login functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.app.config['TESTING'] = True

    @patch("app.controllers.auth_controller.Users")
    def test_login_success_admin(self, mock_users):
        """Admin should login and redirect to admin dashboard."""
        hashed = generate_password_hash("password123")
        mock_users.get_my_email.return_value = {
            'id': 1, 'name': 'Admin User', 'username': 'admin',
            'email': 'admin@test.com', 'password_hash': hashed,
            'role': 'admin', 'profile_pic': None, 'is_banned': 0
        }
        mock_users.is_email_banned.return_value = False

        form_data = {'email': 'admin@test.com', 'password': 'password123'}
        
        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.login()
            
            self.assertEqual(session['user_id'], 1)
            self.assertEqual(session['role'], 'admin')
            self.assertEqual(result.status_code, 302)
            self.assertIn('/admin-dashboard', result.location)

    @patch("app.controllers.auth_controller.Users")
    def test_login_wrong_password(self, mock_users):
        """Should reject wrong password."""
        hashed = generate_password_hash("correctpassword")
        mock_users.get_my_email.return_value = {
            'id': 2, 'name': 'Student', 'username': 'student',
            'email': 'student@test.com', 'password_hash': hashed,
            'role': 'student', 'profile_pic': None, 'is_banned': 0
        }
        mock_users.is_email_banned.return_value = False

        form_data = {'email': 'student@test.com', 'password': 'wrongpassword'}
        
        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.login()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("error", "Incorrect password."), flashes)
            self.assertEqual(result.status_code, 302)

    @patch("app.controllers.auth_controller.Users")
    def test_login_banned_user(self, mock_users):
        """Should reject banned users."""
        hashed = generate_password_hash("password123")
        mock_users.get_my_email.return_value = {
            'id': 3, 'name': 'Banned User', 'username': 'banned',
            'email': 'banned@test.com', 'password_hash': hashed,
            'role': 'student', 'profile_pic': None, 'is_banned': 1
        }
        mock_users.is_email_banned.return_value = False

        form_data = {'email': 'banned@test.com', 'password': 'password123'}
        
        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.login()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('banned' in str(f[1]).lower() for f in flashes))
            self.assertEqual(result.status_code, 302)


class TestAuthControllerRegister(unittest.TestCase):
    """Test AuthController registration functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = AuthController()
        self.app.config['TESTING'] = True

    @patch.object(AuthController, "render")
    @patch("app.controllers.auth_controller.Users")
    @patch("app.controllers.auth_controller.BaseModel")
    def test_register_success(self, mock_base, mock_users, mock_render):
        """Should successfully register new user."""
        mock_render.return_value = "register_page"
        mock_base.fetch_one.return_value = None  # Email not taken
        mock_users.is_username_taken.return_value = False
        mock_users.create_user.return_value = True

        form_data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'john@test.com',
            'password': 'Password123',
            'role': 'student'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.register()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Registration successful! Please login to continue."), flashes)
            self.assertEqual(result.status_code, 302)

    @patch.object(AuthController, "render")
    @patch("app.controllers.auth_controller.BaseModel")
    def test_register_email_already_exists(self, mock_base, mock_render):
        """Should reject if email already registered."""
        mock_render.return_value = "register_page"
        mock_base.fetch_one.return_value = {'id': 1}  # Email exists

        form_data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'existing@test.com',
            'password': 'Password123',
            'role': 'student'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.register()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('already registered' in str(f[1]).lower() for f in flashes))

    @patch.object(AuthController, "render")
    @patch("app.controllers.auth_controller.Users")
    def test_register_weak_password(self, mock_users, mock_render):
        """Should reject password < 6 characters."""
        mock_render.return_value = "register_page"
        mock_users.is_username_taken.return_value = False
        form_data = {
            'name': 'John Doe',
            'username': 'johndoe',
            'email': 'john@test.com',
            'password': '12345',
            'role': 'student'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            result = self.controller.register()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('6 characters' in str(f[1]) for f in flashes))


if __name__ == "__main__":
    unittest.main()
