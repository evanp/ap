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
COLLECTION_ID = f"{ACTOR_ID}/collection/1"
OBJECT_ID = f"{ACTOR_ID}/object/1"
REMOVE_ID = f"{ACTOR_ID}/remove/1"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

COLLECTION = {
    "id": COLLECTION_ID,
    "attributedTo": ACTOR_ID,
    "type": "Collection",
    "name": "A generic collection",
    "totalItems": 1,
    "items": [OBJECT_ID],
}

OBJECT = {
    "id": OBJECT_ID,
    "attributedTo": ACTOR_ID,
    "type": "Object",
    "name": "A generic object",
}

TOKEN_FILE_DATA = json.dumps(
    {"actor_id": "https://social.example/users/evanp", "access_token": "12345678"}
)

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == COLLECTION_ID:
        return MagicMock(status_code=200, json=lambda: COLLECTION)
    elif url == OBJECT_ID:
        return MagicMock(status_code=200, json=lambda: OBJECT)
    else:
        return MagicMock(status_code=404)

def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["outbox"]:
        input_data = json.loads(data)
        added_data = {
            "id": REMOVE_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID
        }
        return MagicMock(
            status_code=200, json=lambda: {**input_data, **added_data}
        )
    else:
        return MagicMock(status_code=404)

class TestRemove(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_remove(
        self, mock_requests_get, mock_requests_post, mock_file
    ):
        run_command(["remove", "--target", COLLECTION_ID, OBJECT_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(REMOVE_ID, sys.stdout.getvalue())