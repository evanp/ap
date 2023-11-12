import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.get import GetCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = 'https://social.example/users/evanp'
NOTE_ID = 'https://social.example/users/evanp/note/1'
ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": "https://social.example/users/evanp/outbox"
}
NOTE = {
    "type": "Note",
    "id": NOTE_ID,
    "content": "Hello World"
}
TOKEN_FILE_DATA = json.dumps({
    "actor_id": ACTOR_ID,
    "access_token": "12345678"
})

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == NOTE_ID:
        return MagicMock(status_code=200, json=lambda: NOTE)
    else:
        return MagicMock(status_code=404)

class TestGetCommand(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch('builtins.open', new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch('requests_oauthlib.OAuth2Session.get', side_effect=mock_oauth_get)
    def test_get_note(self, mock_requests_get, mock_file):
        args = Namespace(id=NOTE_ID, force=False)
        get_cmd = GetCommand(args)

        get_cmd.run()

        # Assertions
        mock_requests_get.assert_called_once()
        self.assertIn(NOTE["content"], sys.stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
