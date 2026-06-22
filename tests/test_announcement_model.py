import unittest
from unittest.mock import patch
from app.models.announcement import Announcement


class TestAnnouncementModel(unittest.TestCase):
    """Test Announcement model functionality."""
    
    @patch("app.models.announcement.Announcement.execute_write")
    def test_add_announcement_success(self, mock_execute):
        """Should add announcement to database."""
        mock_execute.return_value = True

        result = Announcement.add_announcement(
            'Important Notice',
            'Short summary',
            'Academic',
            1,
            'Full announcement body here'
        )
        
        self.assertTrue(result)

    @patch("app.models.announcement.Announcement.fetch_all")
    def test_get_announcement_list(self, mock_fetch):
        """Should retrieve paginated announcements."""
        mock_fetch.return_value = [
            {'id': 1, 'title': 'Announce1', 'category': 'Academic', 'author_name': 'Teacher1'},
            {'id': 2, 'title': 'Announce2', 'category': 'Events', 'author_name': 'Teacher2'}
        ]

        result = Announcement.get_annoucement(0, 10)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['title'], 'Announce1')

    @patch("app.models.announcement.Announcement.fetch_all")
    def test_get_announcement_empty(self, mock_fetch):
        """Should return empty list if no announcements."""
        mock_fetch.return_value = None

        result = Announcement.get_annoucement(0, 10)
        
        self.assertEqual(result, [])

    @patch("app.models.announcement.Announcement.fetch_one")
    def test_get_total_announcement_count(self, mock_fetch):
        """Should return count of announcements."""
        mock_fetch.return_value = {'count': 25}

        result = Announcement.get_total_annoucement_count()
        
        self.assertEqual(result, 25)

    @patch("app.models.announcement.Announcement.fetch_one")
    def test_get_total_announcement_count_none(self, mock_fetch):
        """Should return 0 if count query fails."""
        mock_fetch.return_value = None

        result = Announcement.get_total_annoucement_count()
        
        self.assertEqual(result, 0)

    @patch("app.models.announcement.Announcement.fetch_one")
    def test_get_announcement_by_id(self, mock_fetch):
        """Should retrieve announcement by ID."""
        mock_fetch.return_value = {
            'id': 1, 'title': 'Test Announcement',
            'category': 'Academic', 'body': 'Full content',
            'author_name': 'Teacher'
        }

        result = Announcement.get_annoucement_byid(1)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Test Announcement')

    @patch("app.models.announcement.Announcement.fetch_one")
    def test_get_announcement_by_id_not_found(self, mock_fetch):
        """Should return 0 if announcement not found."""
        mock_fetch.return_value = None

        result = Announcement.get_annoucement_byid(999)
        
        self.assertEqual(result, 0)

    @patch("app.models.announcement.Announcement.execute_write")
    def test_delete_announcement(self, mock_execute):
        """Should delete announcement."""
        mock_execute.return_value = True

        result = Announcement.delete_announcement(1)
        
        self.assertTrue(result)

    @patch("app.models.announcement.Announcement.fetch_all")
    def test_get_latest_announcements(self, mock_fetch):
        """Should retrieve latest announcements."""
        mock_fetch.return_value = [
            {'id': 3, 'title': 'Latest', 'author_name': 'Teacher'},
            {'id': 2, 'title': 'Recent', 'author_name': 'Teacher'},
            {'id': 1, 'title': 'Older', 'author_name': 'Teacher'}
        ]

        result = Announcement.get_latest_announcements(3)
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]['title'], 'Latest')


if __name__ == "__main__":
    unittest.main()
