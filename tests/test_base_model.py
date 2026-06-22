import unittest
from unittest.mock import patch, MagicMock
from app.models.base_model import BaseModel


class TestBaseModel(unittest.TestCase):
    """Test BaseModel ORM methods."""
    
    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_one_success(self, mock_get_conn):
        """Should fetch single record successfully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 1, 'name': 'Test'}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = BaseModel.fetch_one("SELECT * FROM users WHERE id = %s", [1])
        
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['name'], 'Test')
        mock_cursor.execute.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_one_no_connection(self, mock_get_conn):
        """Should return None if connection fails."""
        mock_get_conn.return_value = None

        result = BaseModel.fetch_one("SELECT * FROM users", [])
        
        self.assertIsNone(result)

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_one_not_found(self, mock_get_conn):
        """Should return None if record not found."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = BaseModel.fetch_one("SELECT * FROM users WHERE id = %s", [999])
        
        self.assertIsNone(result)

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_all_success(self, mock_get_conn):
        """Should fetch multiple records successfully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'User1'},
            {'id': 2, 'name': 'User2'},
            {'id': 3, 'name': 'User3'}
        ]
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = BaseModel.fetch_all("SELECT * FROM users")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['name'], 'User1')
        mock_conn.close.assert_called_once()

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_all_empty(self, mock_get_conn):
        """Should return None if no records found."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = BaseModel.fetch_all("SELECT * FROM users WHERE id > %s", [999])
        
        self.assertIsNone(result)

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_execute_write_success(self, mock_get_conn):
        """Should execute write operation successfully."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = BaseModel.execute_write(
            "INSERT INTO users (name, email) VALUES (%s, %s)",
            ['John', 'john@test.com']
        )
        
        self.assertTrue(result)
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_execute_write_no_connection(self, mock_get_conn):
        """Should return False if connection fails."""
        mock_get_conn.return_value = None

        result = BaseModel.execute_write("INSERT INTO users (name) VALUES (%s)", ['John'])
        
        self.assertFalse(result)

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_execute_write_with_exception(self, mock_get_conn):
        """Should return False if execution fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("SQL Error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        with self.assertRaises(Exception):
            BaseModel.execute_write("INSERT INTO users VALUES (%s)", ['bad data'])
        mock_conn.close.assert_called_once()

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_fetch_one_with_params(self, mock_get_conn):
        """Should correctly pass parameters to SQL query."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'id': 5}
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        BaseModel.fetch_one("SELECT * FROM users WHERE id = %s AND role = %s", [5, 'admin'])
        
        # Verify parameters were passed correctly
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM users WHERE id = %s AND role = %s",
            [5, 'admin']
        )

    @patch("app.models.base_model.BaseModel.get_connection")
    def test_connection_closed_on_error(self, mock_get_conn):
        """Connection should be closed even if operation fails."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Query error")
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        try:
            BaseModel.fetch_one("SELECT * FROM users", [])
        except:
            pass
        
        # Connection should still be closed
        mock_conn.close.assert_called()


if __name__ == "__main__":
    unittest.main()
