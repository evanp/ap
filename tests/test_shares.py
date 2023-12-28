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

ANOTHER_ACTOR_ID = "https://social.example/users/another"
AND_ANOTHER_ACTOR_ID = "https://social.example/users/andanother"

SHARE_1_ID = f"{ANOTHER_ACTOR_ID}/shares/1"
SHARE_2_ID = f"{AND_ANOTHER_ACTOR_ID}/shares/2"
SHARE_3_ID = f"{ACTOR_ID}/shares/3"
SHARE_4_ID = f"{OTHER_ID}/shares/4"
SHARE_5_ID = f"{REMOTE_ID}/shares/5"

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

ANOTHER_ACTOR = {
    "type": "Person",
    "id": ANOTHER_ACTOR_ID,
    "preferredUsername": "another",
}

AND_ANOTHER_ACTOR = {
    "type": "Person",
    "id": AND_ANOTHER_ACTOR_ID,
    "preferredUsername": "andanother",
}

SHARE_1 = {
    "type": "Announce",
    "id": SHARE_1_ID,
    "object": OBJECT_ID,
    "actor": ANOTHER_ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

SHARE_2 = {
    "type": "Announce",
    "id": SHARE_2_ID,
    "object": REMOTE_OBJECT_ID,
    "actor": AND_ANOTHER_ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

SHARE_3 = {
    "type": "Announce",
    "id": SHARE_3_ID,
    "object": OBJECT_ID,
    "actor": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

SHARE_4 = {
    "type": "Announce",
    "id": SHARE_4_ID,
    "object": REMOTE_OBJECT_ID,
    "actor": OTHER_ID,
    "published": "2020-01-01T00:00:00Z",
}

SHARE_5 = {
    "type": "Announce",
    "id": SHARE_5_ID,
    "object": OBJECT_ID,
    "actor": REMOTE_ID,
    "published": "2020-01-01T00:00:00Z",
}

SHARES = {
    "id": SHARES_ID,
    "attributedTo": OTHER_ID,
    "type": "Collection",
    "totalItems": 3,
    "items": [
        SHARE_1_ID,
        SHARE_3_ID,
        SHARE_5_ID,
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
    "totalItems": 2,
    "items": [
        SHARE_2_ID,
        SHARE_4_ID,
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
    elif url == SHARE_1_ID:
        return MagicMock(status_code=200, json=lambda: SHARE_1)
    elif url == SHARE_2_ID:
        return MagicMock(status_code=200, json=lambda: SHARE_2)
    elif url == SHARE_3_ID:
        return MagicMock(status_code=200, json=lambda: SHARE_3)
    elif url == SHARE_4_ID:
        return MagicMock(status_code=200, json=lambda: SHARE_4)
    elif url == ANOTHER_ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ANOTHER_ACTOR)
    elif url == AND_ANOTHER_ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: AND_ANOTHER_ACTOR)
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
        if data["id"] == SHARE_5_ID:
            return MagicMock(status_code=200, json=lambda: SHARE_5)
        else:
            return MagicMock(status_code=404)
    else:
        return MagicMock(status_code=404)


class TestLikesCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_shares_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["shares", OBJECT_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertIn(SHARE_1_ID, output)
        self.assertIn(SHARE_3_ID, output)
        self.assertIn(SHARE_5_ID, output)
        self.assertNotIn(SHARE_2_ID, output)
        self.assertNotIn(SHARE_4_ID, output)

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_shares_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["shares", REMOTE_OBJECT_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertNotIn(SHARE_1_ID, output)
        self.assertNotIn(SHARE_3_ID, output)
        self.assertNotIn(SHARE_5_ID, output)
        self.assertIn(SHARE_2_ID, output)
        self.assertIn(SHARE_4_ID, output)


if __name__ == "__main__":
    unittest.main()
