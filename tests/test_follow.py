import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.follow import FollowCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = "https://social.example/users/evanp"
OTHER_1_ID = "https://different.example/users/other1"
OTHER_2_ID = "https://social.example/users/other2"
FOLLOW_ID = f"{ACTOR_ID}/follows/1"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER_1 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "preferredUsername": "other1",
    "inbox": f"{OTHER_1_ID}/inbox",
}

OTHER_2 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "preferredUsername": "other2",
    "inbox": f"{OTHER_2_ID}/inbox",
}

TOKEN_FILE_DATA = json.dumps(
    {"actor_id": "https://social.example/users/evanp", "access_token": "12345678"}
)


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == OTHER_2_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_2)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == OTHER_1_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_1)
        else:
            return MagicMock(status_code=404)
    elif url == ACTOR["outbox"]:
        added_data = {
            "id": FOLLOW_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID,
        }
        return MagicMock(
            status_code=200, json=lambda: {**json.loads(data), **added_data}
        )
    else:
        return MagicMock(status_code=404)


class TestFollowCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_follow_remote(self, mock_requests_get, mock_requests_post, mock_file):
        args = Namespace(subcommand="follow", id=OTHER_1_ID)
        cmd = FollowCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(FOLLOW_ID, sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_follow_local(self, mock_requests_get, mock_requests_post, mock_file):
        args = Namespace(subcommand="follow", id=OTHER_2_ID)
        cmd = FollowCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(FOLLOW_ID, sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
