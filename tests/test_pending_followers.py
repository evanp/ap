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
OTHER_1_ID = "https://different.example/users/other1"
OTHER_2_ID = "https://social.example/users/other2"
PENDING_FOLLOWERS_ID = f"{ACTOR_ID}/followers/pending"
PAGE_2_ID = f"{PENDING_FOLLOWERS_ID}/page/2"
PAGE_1_ID = f"{PENDING_FOLLOWERS_ID}/page/1"
FOLLOW_1_ID = f"{OTHER_1_ID}/follows/1"
FOLLOW_2_ID = f"{OTHER_2_ID}/follows/2"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "inbox": f"{ACTOR_ID}/outbox",
    "pendingFollowers": PENDING_FOLLOWERS_ID,
    "preferredUsername": "evanp",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER_1 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "outbox": f"{OTHER_1_ID}/outbox",
    "inbox": f"{OTHER_1_ID}/inbox",
    "preferredUsername": "other1",
}

OTHER_2 = {
    "type": "Person",
    "id": OTHER_2_ID,
    "outbox": f"{OTHER_2_ID}/outbox",
    "inbox": f"{OTHER_2_ID}/inbox",
    "preferredUsername": "other2",
}

PENDING_FOLLOWERS = {
    "id": PENDING_FOLLOWERS_ID,
    "attributedTo": ACTOR_ID,
    "first": PAGE_2_ID,
}

FOLLOW_1 = {
    "id": FOLLOW_1_ID,
    "actor": OTHER_1_ID,
    "type": "Follow",
    "object": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

FOLLOW_2 = {
    "id": FOLLOW_2_ID,
    "actor": OTHER_2_ID,
    "type": "Follow",
    "object": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": PENDING_FOLLOWERS_ID,
    "next": PAGE_1_ID,
    "orderedItems": [FOLLOW_1],
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": PENDING_FOLLOWERS_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [FOLLOW_2],
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == PENDING_FOLLOWERS_ID:
        return MagicMock(status_code=200, json=lambda: PENDING_FOLLOWERS)
    elif url == PAGE_2_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_2)
    elif url == PAGE_1_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_1)
    elif url == OTHER_2_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_2)
    elif url == FOLLOW_2_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_2)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == OTHER_1_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_1)
        if data["id"] == FOLLOW_1_ID:
            return MagicMock(status_code=200, json=lambda: FOLLOW_1)
        else:
            return MagicMock(status_code=404)
    else:
        return MagicMock(status_code=404)


class TestPendingFollowersCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_pending_followers(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["pending", "followers"], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn("other2@social.example", sys.stdout.getvalue())
        self.assertIn("other1@different.example", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
