import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.delete import DeleteCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session

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

    @patch('builtins.open', new_callable=mock_open, read_data='{"actor_id": "https://social.example/users/evanp", "access_token": "12345678"}')
    @patch('requests_oauthlib.OAuth2Session.post')
    @patch('requests_oauthlib.OAuth2Session.get', side_effect=mock_oauth_get)
    @patch('builtins.input', return_value='y')
    def test_delete_with_confirmation(self, mock_input, mock_requests_get, mock_oauth_post, mock_file):
        args = Namespace(id=NOTE_ID, force=False)
        delete_cmd = DeleteCommand(args)

        mock_requests_get.return_value = MagicMock(status_code=200, json=lambda: {"type": "Note", "content": "Hello World"})
        mock_oauth_post.return_value = MagicMock(status_code=200, json=lambda: {"success": True})

        delete_cmd.run()

        # Assertions
        self.assertEqual(mock_requests_get.call_count, 2)
        mock_oauth_post.assert_called_once()
        mock_input.assert_called_once()
        self.assertIn('Deleted.', sys.stdout.getvalue())

    # Additional tests can be added here

if __name__ == '__main__':
    unittest.main()
