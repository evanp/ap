import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.main import run_command
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json
from ap.version import __version__

USER_AGENT = f"ap/{__version__}"
ACTOR_ID = "https://social.example/users/evanp"
NOTE_ID = "https://social.example/users/evanp/note/1"
ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": "https://social.example/users/evanp/outbox",
}
NOTE = {"type": "Note", "id": NOTE_ID, "content": "Hello World"}
TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})

ACTOR2_ID = "https://social.example/@other"
NOTE2_ID = "https://social.example/@other/123456789012345678"
ACTOR2 = {
    "type": "Person",
    "id": ACTOR2_ID,
    "outbox": "https://social.example/@other/outbox",
}
NOTE2 = {"type": "Note", "id": NOTE2_ID, "content": "Hello World"}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


request_headers = []

def mock_oauth_get(url, headers=None):
    global request_headers
    request_headers.append(headers)
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == NOTE_ID:
        return MagicMock(status_code=200, json=lambda: NOTE)
    elif url == ACTOR2_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR2)
    elif url == NOTE2_ID:
        return MagicMock(status_code=200, json=lambda: NOTE2)
    else:
        return MagicMock(status_code=404)


class TestGetCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_get_note(self, mock_requests_get, mock_file):
        run_command(["get", NOTE_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        mock_requests_get.assert_called_once()
        for headers in request_headers:
            self.assertIn("User-Agent", headers)
            self.assertRegex(headers["User-Agent"], USER_AGENT)
        self.assertIn(NOTE["content"], sys.stdout.getvalue())


    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_get_note_with_at_symbol(self, mock_requests_get, mock_file):
        run_command(["get", NOTE2_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        mock_requests_get.assert_called_once()
        self.assertIn(NOTE2["content"], sys.stdout.getvalue())

if __name__ == "__main__":
    unittest.main()
