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
import logging

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
ACTOR_WEBFINGER_ID = "evanp@social.example"
ACTOR_WEBFINGER_JSON = {
    "subject": "acct:evanp@social.example",
    "links": [{"rel": "self",
               "type": "application/activity+json",
               "href": ACTOR_ID}]
}

WEBFINGER_URL_BASE = "https://social.example/.well-known/webfinger"
ACTOR_WEBFINGER_URL = WEBFINGER_URL_BASE + "?resource=acct%3Aevanp%40social.example"

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


def mock_requests_get(url, **kwargs):
    if url == WEBFINGER_URL_BASE:
        return MagicMock(
            status_code=200,
            headers={"Content-Type": "application/jrd+json"},
            json=lambda: ACTOR_WEBFINGER_JSON,
        )
    else:
        return MagicMock(status_code=404)


class TestGetCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout
        self.log_stream = io.StringIO()
        logging.basicConfig(level=logging.DEBUG, stream=self.log_stream)

    def tearDown(self):
        sys.stdout = self.held
        # print(self.log_stream.getvalue())

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

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_get_actor(self, mock_requests_get, mock_file):
        run_command(["get", ACTOR_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        mock_requests_get.assert_called_once()
        for headers in request_headers:
            self.assertIn("User-Agent", headers)
            self.assertRegex(headers["User-Agent"], USER_AGENT)
        self.assertIn(ACTOR['type'], sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    @patch('requests.get', side_effect=mock_requests_get)
    def test_get_webfinger(self, mock_requests_get, mock_oauth_get, mock_file):
        run_command(["get", ACTOR_WEBFINGER_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        mock_oauth_get.assert_called_once()
        mock_requests_get.assert_called_once()
        for headers in request_headers:
            self.assertIn("User-Agent", headers)
            self.assertRegex(headers["User-Agent"], USER_AGENT)
        self.assertIn(ACTOR_ID, sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
