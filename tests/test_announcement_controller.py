import unittest
from unittest.mock import patch, MagicMock
from flask import Flask, Blueprint, session, get_flashed_messages
from app.controllers.announcement_controller import AnnouncementController


def make_test_app():
    app = Flask(__name__)
    app.secret_key = "test-secret-key"

    bp = Blueprint("announce", __name__)
    bp.route("/announcements", endpoint="announcement")(lambda: "announcements")
    bp.route("/announcements/<announcement_id>", endpoint="announcement_view")(lambda announcement_id: "view")
    app.register_blueprint(bp)
    return app


class TestAnnouncementController(unittest.TestCase):
    """Test AnnouncementController functionality."""
    
    def setUp(self):
        self.app = make_test_app()
        self.controller = AnnouncementController()
        self.app.config['TESTING'] = True
        self.auth_patch = patch("app.auth.Users.is_user_banned", return_value=False)
        self.auth_patch.start()

    def tearDown(self):
        self.auth_patch.stop()

    @patch("app.controllers.announcement_controller.Announcement")
    @patch.object(AnnouncementController, "render")
    def test_announcement_list_pagination(self, mock_render, mock_announcement):
        """Should fetch and paginate announcements correctly."""
        mock_render.return_value = "announcements_page"
        mock_announcement.get_annoucement.return_value = [
            {'id': 1, 'title': 'Announcement 1', 'category': 'Academic', 'author_name': 'Teacher1'},
            {'id': 2, 'title': 'Announcement 2', 'category': 'Events', 'author_name': 'Teacher2'}
        ]
        mock_announcement.get_total_annoucement_count.return_value = 2

        with self.app.test_request_context('/?page=1', method="GET"):
            session['user_id'] = 1
            session['username'] = 'testuser'
            session['email'] = 'test@test.com'
            session['role'] = 'student'
            
            result = self.controller.announcement()
            
            self.assertEqual(result, "announcements_page")
            # Verify it called with correct pagination
            mock_announcement.get_annoucement.assert_called_once_with(0, 10)
            mock_announcement.get_total_annoucement_count.assert_called_once()

    @patch("app.controllers.announcement_controller.Announcement")
    @patch.object(AnnouncementController, "render")
    def test_announcement_view_single(self, mock_render, mock_announcement):
        """Should fetch and display single announcement."""
        mock_render.return_value = "single_announcement_page"
        mock_announcement.get_annoucement_byid.return_value = {
            'id': 1, 'title': 'Important Notice', 'category': 'Academic',
            'body': 'This is important', 'author_name': 'Principal'
        }

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 1
            session['role'] = 'student'
            
            result = self.controller.announcement_view(1)
            
            self.assertEqual(result, "single_announcement_page")
            mock_announcement.get_annoucement_byid.assert_called_once_with(1)

    @patch("app.controllers.announcement_controller.Announcement")
    def test_announcement_create_teacher(self, mock_announcement):
        """Teacher should be able to create announcement."""
        mock_announcement.add_announcement.return_value = True

        form_data = {
            'title': 'New Announcement',
            'category': 'Academic',
            'summary': 'Short summary',
            'description': 'Full description here'
        }

        with self.app.test_request_context(method="POST", data=form_data):
            session['user_id'] = 5
            session['username'] = 'teacher'
            session['role'] = 'teacher'
            
            result = self.controller.announcement_create()
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertIn(("success", "Succesfully added the annoucements !"), flashes)
            mock_announcement.add_announcement.assert_called_once_with(
                'New Announcement',
                'Short summary',
                'Academic',
                5,
                'Full description here'
            )

    @patch("app.controllers.announcement_controller.Announcement")
    def test_announcement_delete_owner_only(self, mock_announcement):
        """Only announcement owner (or admin) can delete."""
        mock_announcement.get_annoucement_byid.return_value = {
            'id': 1, 'title': 'To Delete', 'author_id': 5
        }

        with self.app.test_request_context(method="GET"):
            session['user_id'] = 999  # Different user
            session['role'] = 'teacher'
            
            result = self.controller.announcement_delete(1)
            
            flashes = get_flashed_messages(with_categories=True)
            self.assertTrue(any('own announcements' in str(f[1]).lower() for f in flashes))


if __name__ == "__main__":
    unittest.main()
