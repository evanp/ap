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
OTHER_ID = "https://social.example/users/other"
OBJECT_ID = f"{OTHER_ID}/objects/1"
SHARES_ID = f"{OBJECT_ID}/shares"
REMOTE_ID = "https://remote.example/users/other"
REMOTE_OBJECT_ID = f"{REMOTE_ID}/objects/1"
REMOTE_SHARES_ID = f"{REMOTE_OBJECT_ID}/shares"
SHARE_ID = f"{ACTOR_ID}/shares/1"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "preferredUsername": "evanp",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER = {
    "type": "Person",
    "id": OTHER_ID,
    "preferredUsername": "other",
}

OBJECT = {
    "type": "Note",
    "id": OBJECT_ID,
    "shares": SHARES_ID,
    "attributedTo": OTHER_ID,
    "content": "This is a note",
}

SHARES = {
    "id": SHARES_ID,
    "attributedTo": OTHER_ID,
    "type": "Collection",
    "totalItems": 0,
    "items": [
    ]
}

REMOTE = {
    "type": "Person",
    "id": REMOTE_ID,
    "preferredUsername": "other",
}

REMOTE_OBJECT = {
    "type": "Object",
    "id": REMOTE_OBJECT_ID,
    "attributedTo": REMOTE_ID,
    "shares": REMOTE_SHARES_ID,
}

REMOTE_SHARES = {
    "id": REMOTE_SHARES_ID,
    "attributedTo": REMOTE_ID,
    "type": "Collection",
    "totalItems": 0,
    "items": [
    ]
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == OTHER_ID:
        return MagicMock(status_code=200, json=lambda: OTHER)
    elif url == OBJECT_ID:
        return MagicMock(status_code=200, json=lambda: OBJECT)
    elif url == SHARES_ID:
        return MagicMock(status_code=200, json=lambda: SHARES)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == REMOTE_ID:
            return MagicMock(status_code=200, json=lambda: REMOTE)
        if data["id"] == REMOTE_OBJECT_ID:
            return MagicMock(status_code=200, json=lambda: REMOTE_OBJECT)
        if data["id"] == REMOTE_SHARES_ID:
            return MagicMock(status_code=200, json=lambda: REMOTE_SHARES)
        else:
            return MagicMock(status_code=404)
    elif url == ACTOR["outbox"]:
        data = json.loads(data)
        added_data = {
            "id": SHARE_ID,
            "actor": ACTOR_ID,
            "published": "2020-01-01T00:00:00Z",
        }
        result = {**data, **added_data}
        return MagicMock(status_code=200, json=lambda: result)
    else:
        return MagicMock(status_code=404)


class TestSharesCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_share_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["share", OBJECT_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertIn(SHARE_ID, output)

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_shares_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["share", REMOTE_OBJECT_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertIn(SHARE_ID, output)


if __name__ == "__main__":
    unittest.main()
