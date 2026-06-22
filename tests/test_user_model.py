import unittest
from unittest.mock import patch, MagicMock
from app.models.user import Users


class TestUsersModel(unittest.TestCase):
    """Test Users model functionality."""
    
    @patch("app.models.user.Users.fetch_one")
    def test_get_my_email_found(self, mock_fetch):
        """Should retrieve user by email."""
        mock_fetch.return_value = {
            'id': 1, 'name': 'John Doe', 'username': 'john',
            'email': 'john@test.com', 'password_hash': 'hashed_pwd',
            'role': 'student', 'is_banned': 0
        }

        result = Users.get_my_email('john@test.com')
        
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['role'], 'student')

    @patch("app.models.user.Users.fetch_one")
    def test_get_my_email_not_found(self, mock_fetch):
        """Should return None if email not found."""
        mock_fetch.return_value = None

        result = Users.get_my_email('nonexistent@test.com')
        
        self.assertIsNone(result)

    @patch("app.models.user.Users.execute_write")
    def test_reset_password_success(self, mock_execute):
        """Should update password successfully."""
        mock_execute.return_value = True

        result = Users.reset_password('user@test.com', 'new_hash')
        
        self.assertTrue(result)

    @patch("app.models.user.Users.fetch_one")
    def test_is_username_taken_yes(self, mock_fetch):
        """Should detect if username is already taken."""
        mock_fetch.return_value = {'id': 5}

        result = Users.is_username_taken('john_doe')
        
        self.assertTrue(result)

    @patch("app.models.user.Users.fetch_one")
    def test_is_username_taken_no(self, mock_fetch):
        """Should return False if username is available."""
        mock_fetch.return_value = None

        result = Users.is_username_taken('available_user')
        
        self.assertFalse(result)

    @patch("app.models.user.Users.execute_write")
    def test_create_user_success(self, mock_execute):
        """Should create new user successfully."""
        mock_execute.return_value = True

        result = Users.create_user('John Doe', 'johndoe', 'john@test.com', 'hashed', 'student')
        
        self.assertTrue(result)

    @patch("app.models.user.Users.execute_write")
    def test_create_user_duplicate_email(self, mock_execute):
        """Should return False if unique constraint violated."""
        mock_execute.side_effect = Exception("Duplicate entry")

        result = Users.create_user('Jane Doe', 'janedoe', 'jane@test.com', 'hashed', 'student')
        
        self.assertFalse(result)

    @patch("app.models.user.Users.fetch_all")
    def test_get_all_students(self, mock_fetch):
        """Should retrieve all students."""
        mock_fetch.return_value = [
            {'id': 1}, {'id': 2}, {'id': 3}
        ]

        result = Users.get_all_students()
        
        self.assertEqual(len(result), 3)

    @patch("app.models.user.Users.fetch_all")
    def test_get_all_students_empty(self, mock_fetch):
        """Should return empty list if no students."""
        mock_fetch.return_value = None

        result = Users.get_all_students()
        
        self.assertEqual(result, [])

    @patch("app.models.user.Users.fetch_one")
    def test_get_user_by_id(self, mock_fetch):
        """Should retrieve user details by ID."""
        mock_fetch.return_value = {
            'id': 1, 'name': 'John', 'username': 'john',
            'email': 'john@test.com', 'role': 'student'
        }

        result = Users.get_user_by_id(1)
        
        self.assertEqual(result['name'], 'John')

    @patch("app.models.user.Users.execute_write")
    def test_ban_user(self, mock_execute):
        """Should ban a user."""
        mock_execute.return_value = True

        result = Users.ban_user(5)
        
        self.assertTrue(result)

    @patch("app.models.user.Users.execute_write")
    def test_unban_user(self, mock_execute):
        """Should unban a user."""
        mock_execute.return_value = True

        result = Users.unban_user(5)
        
        self.assertTrue(result)

    @patch("app.models.user.Users.fetch_one")
    def test_is_user_banned_true(self, mock_fetch):
        """Should identify banned users."""
        mock_fetch.return_value = {'is_banned': 1}

        result = Users.is_user_banned(1)
        
        self.assertTrue(result)

    @patch("app.models.user.Users.fetch_one")
    def test_is_user_banned_false(self, mock_fetch):
        """Should identify active users."""
        mock_fetch.return_value = {'is_banned': 0}

        result = Users.is_user_banned(1)
        
        self.assertFalse(result)

    @patch("app.models.user.Users.fetch_one")
    def test_get_stats(self, mock_fetch):
        """Should retrieve user statistics."""
        mock_fetch.side_effect = [
            {'total': 100},  # total users
            {'total': 70},   # students
            {'total': 25},   # teachers
            {'total': 5},    # admins
            {'total': 2},    # banned
            {'total': 3},    # new today
        ]

        result = Users.get_stats()
        
        self.assertEqual(result['total'], 100)
        self.assertEqual(result['students'], 70)
        self.assertEqual(result['banned'], 2)


if __name__ == "__main__":
    unittest.main()
