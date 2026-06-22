import unittest
from unittest.mock import patch, MagicMock
from app.models.task import Task, TaskBookmark


class TestTaskModel(unittest.TestCase):
    """Test Task model functionality."""
    
    @patch("app.models.task.Task.get_connection")
    def test_create_task_success(self, mock_get_conn):
        """Should create task and return task ID."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        result = Task.create_task(
            'Math Homework', 'Solve problems', 1, '2026-07-01', None, 'Math'
        )
        
        self.assertEqual(result, 42)
        mock_conn.commit.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("app.models.task.Task.fetch_all")
    def test_get_teacher_tasks(self, mock_fetch):
        """Should retrieve all tasks for a teacher."""
        mock_fetch.return_value = [
            {'id': 1, 'title': 'Task1', 'created_by': 5},
            {'id': 2, 'title': 'Task2', 'created_by': 5}
        ]

        result = Task.get_teacher_tasks(5)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Task1')

    @patch("app.models.task.Task.fetch_all")
    def test_get_teacher_tasks_empty(self, mock_fetch):
        """Should return empty list if teacher has no tasks."""
        mock_fetch.return_value = None

        result = Task.get_teacher_tasks(999)
        
        self.assertEqual(result, [])

    @patch("app.models.task.Task.fetch_all")
    def test_get_today_tasks(self, mock_fetch):
        """Should retrieve today's tasks for student."""
        mock_fetch.return_value = [
            {'id': 1, 'title': 'Task Due Today', 'due_date': '2026-06-22'}
        ]

        result = Task.get_today_tasks(10)
        
        self.assertEqual(len(result), 1)

    @patch("app.models.task.Task.fetch_one")
    def test_get_task_by_id(self, mock_fetch):
        """Should retrieve single task by ID."""
        mock_fetch.return_value = {
            'id': 5, 'title': 'Specific Task', 'description': 'Details'
        }

        result = Task.get_task(5)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Specific Task')


class TestTaskBookmarkModel(unittest.TestCase):
    """Test TaskBookmark model functionality."""
    
    @patch("app.models.task.TaskBookmark.execute_write")
    def test_snapshot_task_success(self, mock_execute):
        """Should create snapshot of task."""
        mock_execute.return_value = True

        task = {
            'id': 1, 'title': 'Task', 'description': 'Desc',
            'subject': 'Math', 'due_date': '2026-07-01',
            'attached_filename': 'file.pdf', 'created_by': 5,
            'created_at': '2026-06-20 10:00:00'
        }

        TaskBookmark.snapshot_task(task)
        
        mock_execute.assert_called_once()

    def test_snapshot_task_none(self):
        """Should handle None task gracefully."""
        # Should not raise error
        result = TaskBookmark.snapshot_task(None)
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
