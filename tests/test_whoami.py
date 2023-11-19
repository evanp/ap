import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.commands.whoami import WhoamiCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = "https://social.example/users/evanp"
ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": "https://social.example/users/evanp/outbox",
    "preferredUsername": "evanp",
}
TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    else:
        return MagicMock(status_code=404)


class TestWhoamiCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_whoami(self, mock_requests_get, mock_file):
        args = Namespace(subcommand="whoami")
        delete_cmd = WhoamiCommand(args)

        delete_cmd.run()

        # Assertions
        mock_requests_get.assert_called_once()
        self.assertIn("evanp@social.example", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
