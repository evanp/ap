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
LIKES_ID = f"{OBJECT_ID}/likes"
REMOTE_ID = "https://remote.example/users/other"
REMOTE_OBJECT_ID = f"{REMOTE_ID}/objects/1"
REMOTE_LIKES_ID = f"{REMOTE_OBJECT_ID}/likes"

ANOTHER_ACTOR_ID = "https://social.example/users/another"
AND_ANOTHER_ACTOR_ID = "https://social.example/users/andanother"

LIKE_1_ID = f"{ANOTHER_ACTOR_ID}/likes/1"
LIKE_2_ID = f"{AND_ANOTHER_ACTOR_ID}/likes/2"
LIKE_3_ID = f"{ACTOR_ID}/likes/3"
LIKE_4_ID = f"{OTHER_ID}/likes/4"
LIKE_5_ID = f"{REMOTE_ID}/likes/5"

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
    "likes": LIKES_ID,
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

LIKE_1 = {
    "type": "Like",
    "id": LIKE_1_ID,
    "object": OBJECT_ID,
    "actor": ANOTHER_ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

LIKE_2 = {
    "type": "Like",
    "id": LIKE_2_ID,
    "object": REMOTE_OBJECT_ID,
    "actor": AND_ANOTHER_ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

LIKE_3 = {
    "type": "Like",
    "id": LIKE_3_ID,
    "object": OBJECT_ID,
    "actor": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
}

LIKE_4 = {
    "type": "Like",
    "id": LIKE_4_ID,
    "object": REMOTE_OBJECT_ID,
    "actor": OTHER_ID,
    "published": "2020-01-01T00:00:00Z",
}

LIKE_5 = {
    "type": "Like",
    "id": LIKE_5_ID,
    "object": OBJECT_ID,
    "actor": REMOTE_ID,
    "published": "2020-01-01T00:00:00Z",
}

LIKES = {
    "id": LIKES_ID,
    "attributedTo": OTHER_ID,
    "type": "Collection",
    "totalItems": 3,
    "items": [
        LIKE_1_ID,
        LIKE_3_ID,
        LIKE_5_ID,
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
    "likes": REMOTE_LIKES_ID,
}

REMOTE_LIKES = {
    "id": REMOTE_LIKES_ID,
    "attributedTo": REMOTE_ID,
    "type": "Collection",
    "totalItems": 2,
    "items": [
        LIKE_2_ID,
        LIKE_4_ID,
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
    elif url == LIKES_ID:
        return MagicMock(status_code=200, json=lambda: LIKES)
    elif url == LIKE_1_ID:
        return MagicMock(status_code=200, json=lambda: LIKE_1)
    elif url == LIKE_2_ID:
        return MagicMock(status_code=200, json=lambda: LIKE_2)
    elif url == LIKE_3_ID:
        return MagicMock(status_code=200, json=lambda: LIKE_3)
    elif url == LIKE_4_ID:
        return MagicMock(status_code=200, json=lambda: LIKE_4)
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
        if data["id"] == REMOTE_LIKES_ID:
            return MagicMock(status_code=200, json=lambda: REMOTE_LIKES)
        if data["id"] == LIKE_5_ID:
            return MagicMock(status_code=200, json=lambda: LIKE_5)
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
    def test_likes_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["likes", OBJECT_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertIn(LIKE_1_ID, output)
        self.assertIn(LIKE_3_ID, output)
        self.assertIn(LIKE_5_ID, output)
        self.assertNotIn(LIKE_2_ID, output)
        self.assertNotIn(LIKE_4_ID, output)

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_likes_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["likes", REMOTE_OBJECT_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertNotIn(LIKE_1_ID, output)
        self.assertNotIn(LIKE_3_ID, output)
        self.assertNotIn(LIKE_5_ID, output)
        self.assertIn(LIKE_2_ID, output)
        self.assertIn(LIKE_4_ID, output)


if __name__ == "__main__":
    unittest.main()
