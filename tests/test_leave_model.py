import unittest
from unittest.mock import patch
from datetime import date, timedelta
from app.models.leave_request import LeaveRequest


class TestLeaveRequestModel(unittest.TestCase):
    """Test LeaveRequest model functionality."""
    
    @patch("app.models.leave_request.LeaveRequest.execute_write")
    def test_create_leave_request_success(self, mock_execute):
        """Should create leave request."""
        mock_execute.return_value = True

        result = LeaveRequest.create(
            1, date.today(), date.today(), 'sick', 'I am feeling unwell'
        )
        
        self.assertTrue(result)

    @patch("app.models.leave_request.LeaveRequest.fetch_all")
    def test_get_by_user_all_statuses(self, mock_fetch):
        """Should retrieve all leave requests for user."""
        mock_fetch.return_value = [
            {'id': 1, 'status': 'pending', 'leave_type': 'sick'},
            {'id': 2, 'status': 'approved', 'leave_type': 'personal'}
        ]

        result = LeaveRequest.get_by_user(1)
        
        self.assertEqual(len(result), 2)

    @patch("app.models.leave_request.LeaveRequest.fetch_all")
    def test_get_by_user_pending_filter(self, mock_fetch):
        """Should filter leave requests by status."""
        mock_fetch.return_value = [
            {'id': 1, 'status': 'pending'}
        ]

        result = LeaveRequest.get_by_user(1, 'pending')
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['status'], 'pending')

    @patch("app.models.leave_request.LeaveRequest.fetch_all")
    def test_get_by_user_no_requests(self, mock_fetch):
        """Should return empty list if no requests."""
        mock_fetch.return_value = None

        result = LeaveRequest.get_by_user(999)
        
        self.assertEqual(result, [])

    @patch("app.models.leave_request.LeaveRequest.fetch_all")
    def test_get_all_requests_admin_view(self, mock_fetch):
        """Should retrieve all leave requests (admin view)."""
        mock_fetch.return_value = [
            {'id': 1, 'student_name': 'Student1', 'status': 'pending'},
            {'id': 2, 'student_name': 'Student2', 'status': 'approved'}
        ]

        result = LeaveRequest.get_all_requests()
        
        self.assertEqual(len(result), 2)

    @patch("app.models.leave_request.LeaveRequest.fetch_one")
    def test_get_by_id(self, mock_fetch):
        """Should retrieve single leave request."""
        mock_fetch.return_value = {
            'id': 1, 'user_id': 5, 'status': 'pending',
            'leave_type': 'sick'
        }

        result = LeaveRequest.get_by_id(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], 'pending')

    @patch("app.models.leave_request.LeaveRequest.execute_write")
    def test_update_status(self, mock_execute):
        """Should update leave request status."""
        mock_execute.return_value = True

        result = LeaveRequest.update_status(1, 'approved')
        
        self.assertTrue(result)

    @patch("app.models.leave_request.LeaveRequest.execute_write")
    def test_delete_pending_request(self, mock_execute):
        """Should delete a pending leave request."""
        mock_execute.return_value = True

        result = LeaveRequest.delete_pending(1, 1)
        
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
