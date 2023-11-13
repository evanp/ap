import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.outbox import OutboxCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = "https://social.example/users/evanp"
OUTBOX_ID = f"{ACTOR_ID}/outbox"
PAGE_2_ID = f"{OUTBOX_ID}/page/2"
PAGE_1_ID = f"{OUTBOX_ID}/page/1"

OUTBOX = {"id": OUTBOX_ID, "attributedTo": ACTOR_ID, "first": PAGE_2_ID}

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": OUTBOX,
    "inbox": f"{ACTOR_ID}/inbox",
    "preferredUsername": "evanp",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": OUTBOX_ID,
    "next": PAGE_1_ID,
    "orderedItems": [
        {
            "type": "Activity",
            "id": f"{ACTOR_ID}/activity/11",
            "summary": "Page 2 Activity 11",
        }
    ],
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": OUTBOX_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [
        {
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
    elif url == OUTBOX_ID:
        return MagicMock(status_code=200, json=lambda: OUTBOX)
    elif url == PAGE_2_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_2)
    elif url == PAGE_1_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_1)
    else:
        return MagicMock(status_code=404)


class TestOutboxCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_outbox(self, mock_requests_get, mock_file):
        args = Namespace(subcommand="outbox", limit=10, offset=0)
        outbox_cmd = OutboxCommand(args)

        outbox_cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertIn("Page 1 Activity 10", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
