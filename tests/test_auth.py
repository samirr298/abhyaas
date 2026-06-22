import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session
from app.auth import login_required, role_required


def make_test_app():
    """Create a test Flask app with necessary routes."""
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("auth", __name__)
    bp.route("/login", endpoint="login")(lambda: "login")
    bp.route("/dashboard", endpoint="dashboard")(lambda: "dashboard")
    bp.route("/admin", endpoint="admin")(lambda: "admin")
    app.register_blueprint(bp)
    return app


class TestLoginRequired(unittest.TestCase):
    """Test the login_required decorator."""
    
    def setUp(self):
        self.app = make_test_app()

    @patch("app.auth.Users")
    def test_login_required_redirects_without_session(self, mock_users):
        """Decorator should redirect unauthenticated users to login."""
        @login_required
        def protected_route():
            return "success"

        with self.app.test_request_context(method="GET"):
            result = protected_route()
            # Should redirect to login
            self.assertEqual(result.status_code, 302)
            self.assertIn("login", result.location)

    @patch("app.auth.Users")
    def test_login_required_allows_valid_user(self, mock_users):
        """Decorator should allow authenticated users through."""
        mock_users.is_user_banned.return_value = False

        @login_required
        def protected_route():
            return "success"

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 123
            result = protected_route()
            # Should execute the function
            self.assertEqual(result, "success")

    @patch("app.auth.Users")
    def test_login_required_kicks_out_banned_user(self, mock_users):
        """Decorator should redirect banned users even if logged in."""
        mock_users.is_user_banned.return_value = True

        @login_required
        def protected_route():
            return "should not reach"

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 999
            result = protected_route()
            # Should redirect to login
            self.assertEqual(result.status_code, 302)
            self.assertIn("login", result.location)


class TestRoleRequired(unittest.TestCase):
    """Test the role_required decorator."""
    
    def setUp(self):
        self.app = make_test_app()

    def test_role_required_denies_wrong_role(self):
        """Decorator should deny users with wrong role."""
        @role_required('admin')
        def admin_only():
            return "admin success"

        with self.app.test_request_context(method="GET"):
            session['role'] = 'student'
            result = admin_only()
            # Should redirect
            self.assertEqual(result.status_code, 302)

    def test_role_required_allows_correct_role(self):
        """Decorator should allow users with correct role."""
        @role_required('admin')
        def admin_only():
            return "admin success"

        with self.app.test_request_context(method="GET"):
            session['role'] = 'admin'
            result = admin_only()
            # Should execute
            self.assertEqual(result, "admin success")

    def test_role_required_allows_admin_for_any_role(self):
        """Admins should bypass role restrictions."""
        @role_required('teacher')
        def teacher_only():
            return "teacher success"

        with self.app.test_request_context(method="GET"):
            session['role'] = 'admin'
            result = teacher_only()
            # Should execute even though admin != teacher
            self.assertEqual(result, "teacher success")


if __name__ == "__main__":
    unittest.main()
