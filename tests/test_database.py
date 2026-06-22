import unittest
from unittest.mock import patch, MagicMock
from app.database import Database


class TestDatabaseConnection(unittest.TestCase):
    """Test Database connection functionality."""
    
    @patch("app.database.pymysql.connect")
    def test_db_connection_success(self, mock_connect):
        """Should establish database connection."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        result = Database.db()
        
        self.assertIsNotNone(result)
        mock_connect.assert_called_once()

    @patch("app.database.pymysql.connect")
    def test_db_connection_with_correct_params(self, mock_connect):
        """Should use correct connection parameters."""
        mock_conn = MagicMock()
        mock_connect.return_value = mock_conn

        with patch("app.database.config") as mock_config:
            mock_config.MYSQL_HOST = "localhost"
            mock_config.MYSQL_USER = "root"
            mock_config.MYSQL_PASSWORD = "password"
            mock_config.MYSQL_DATABASE = "abhyas"

            Database.db()
            
            # Verify connection was called with correct parameters
            mock_connect.assert_called_once()

    @patch("app.database.Database.db")
    def test_create_users_table(self, mock_db):
        """Should create users table if not exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.return_value = mock_conn

        Database.create_users_table()
        
        # Verify cursor execute was called
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    @patch("app.database.Database.db")
    def test_create_attendance_table(self, mock_db):
        """Should create attendance table if not exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.return_value = mock_conn

        Database.create_attendance_table()
        
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()

    @patch("app.database.Database.db")
    def test_create_announcement_table(self, mock_db):
        """Should create announcements table if not exists."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_db.return_value = mock_conn

        Database.create_announcement_table()
        
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
