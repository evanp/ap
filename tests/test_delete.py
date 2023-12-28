import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.main import run_command
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = "https://social.example/users/evanp"
NOTE_ID = "https://social.example/users/evanp/note/1"
ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": "https://social.example/users/evanp/outbox",
}
NOTE = {"type": "Note", "id": NOTE_ID, "content": "Hello World"}
TOKEN_FILE_DATA = json.dumps(
    {"actor_id": "https://social.example/users/evanp", "access_token": "12345678"}
)


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == NOTE_ID:
        return MagicMock(status_code=200, json=lambda: NOTE)
    else:
        return MagicMock(status_code=404)


class TestDeleteCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post")
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    @patch("builtins.input", return_value="y")
    def test_delete_with_confirmation(
        self, mock_input, mock_requests_get, mock_oauth_post, mock_file
    ):

        mock_oauth_post.return_value = MagicMock(
            status_code=200, json=lambda: {"success": True}
        )

        run_command(["delete", NOTE_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertEqual(mock_requests_get.call_count, 2)
        mock_oauth_post.assert_called_once()
        mock_input.assert_called_once()
        self.assertIn("Deleted.", sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post")
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    @patch("builtins.input", return_value="y")
    def test_delete_with_force(
        self, mock_input, mock_requests_get, mock_oauth_post, mock_file
    ):

        mock_oauth_post.return_value = MagicMock(
            status_code=200, json=lambda: {"success": True}
        )

        run_command(["delete", "--force", NOTE_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertEqual(mock_requests_get.call_count, 2)
        mock_oauth_post.assert_called_once()
        self.assertEqual(mock_input.call_count, 0)
        self.assertIn("Deleted.", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
