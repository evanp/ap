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
OTHER_ID = "https://different.example/users/other"
INBOX_ID = f"{ACTOR_ID}/inbox"
PAGE_2_ID = f"{INBOX_ID}/page/2"
PAGE_1_ID = f"{INBOX_ID}/page/1"

INBOX = {"id": INBOX_ID, "attributedTo": ACTOR_ID, "first": PAGE_2_ID}

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "inbox": INBOX,
    "preferredUsername": "evanp",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER = {
    "type": "Person",
    "id": OTHER_ID,
    "outbox": f"{OTHER_ID}/outbox",
    "inbox": f"{OTHER_ID}/inbox",
    "preferredUsername": "other",
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": INBOX_ID,
    "next": PAGE_1_ID,
    "orderedItems": [
        {
            "actor": OTHER_ID,
            "type": "Activity",
            "id": f"{OTHER_ID}/activity/11",
            "summary": "Page 2 Activity 11",
        }
    ],
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": INBOX_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [
        {
            "actor": ACTOR_ID,
            "type": "Activity",
            "id": f"{ACTOR_ID}/activity/10",
            "summary": "Page 1 Activity 10",
        }
    ],
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == INBOX_ID:
        return MagicMock(status_code=200, json=lambda: INBOX)
    elif url == PAGE_2_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_2)
    elif url == PAGE_1_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_1)
    elif url == OTHER_ID:
        return MagicMock(status_code=200, json=lambda: OTHER)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == OTHER_ID:
            return MagicMock(status_code=200, json=lambda: OTHER)
        else:
            return MagicMock(status_code=404)
    else:
        return MagicMock(status_code=404)


class TestInboxCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_inbox(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["inbox"], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn("Page 1 Activity 10", sys.stdout.getvalue())
        self.assertIn("evanp@social.example", sys.stdout.getvalue())
        self.assertIn("other@different.example", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
