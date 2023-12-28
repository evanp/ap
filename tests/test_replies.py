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
REPLIES_ID = f"{OBJECT_ID}/replies"
REMOTE_ID = "https://remote.example/users/other"
REMOTE_OBJECT_ID = f"{REMOTE_ID}/objects/1"
REMOTE_REPLIES_ID = f"{REMOTE_OBJECT_ID}/replies"

ANOTHER_ACTOR_ID = "https://social.example/users/another"
AND_ANOTHER_ACTOR_ID = "https://social.example/users/andanother"

REPLY_1_ID = f"{ANOTHER_ACTOR_ID}/objects/1"
REPLY_2_ID = f"{AND_ANOTHER_ACTOR_ID}/objects/2"
REPLY_3_ID = f"{ACTOR_ID}/objects/3"
REPLY_4_ID = f"{OTHER_ID}/objects/4"
REPLY_5_ID = f"{REMOTE_ID}/objects/5"

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
    "replies": REPLIES_ID,
    "attributedTo": OTHER_ID,
    "contentMap": {
        "en": "This is a note"
    }
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

REPLY_1 = {
    "type": "Note",
    "id": REPLY_1_ID,
    "inReplyTo": OBJECT_ID,
    "attributedTo": ANOTHER_ACTOR_ID,
    "contentMap": {
        "en": "You're doing it wrong."
    },
    "published": "2020-01-01T00:00:00Z",
}

REPLY_2 = {
    "type": "Note",
    "id": REPLY_2_ID,
    "inReplyTo": REMOTE_OBJECT_ID,
    "attributedTo": AND_ANOTHER_ACTOR_ID,
    "contentMap": {
        "en": "You're doing it wrong."
    },
    "published": "2020-01-01T00:00:00Z",
}

REPLY_3 = {
    "type": "Note",
    "id": REPLY_3_ID,
    "inReplyTo": OBJECT_ID,
    "attributedTo": ACTOR_ID,
    "contentMap": {
        "en": "You're doing it wrong."
    },
    "published": "2020-01-01T00:00:00Z",
}

REPLY_4 = {
    "type": "Note",
    "id": REPLY_4_ID,
    "inReplyTo": REMOTE_OBJECT_ID,
    "attributedTo": OTHER_ID,
    "contentMap": {
        "en": "You're doing it wrong."
    },
    "published": "2020-01-01T00:00:00Z",
}

REPLY_5 = {
    "type": "Note",
    "id": REPLY_5_ID,
    "inReplyTo": OBJECT_ID,
    "attributedTo": REMOTE_ID,
    "contentMap": {
        "en": "You're doing it wrong."
    },
    "published": "2020-01-01T00:00:00Z",
}

REPLIES = {
    "id": REPLIES_ID,
    "attributedTo": OTHER_ID,
    "type": "Collection",
    "totalItems": 3,
    "items": [
        REPLY_1_ID,
        REPLY_3_ID,
        REPLY_5_ID,
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
    "replies": REMOTE_REPLIES_ID,
}

REMOTE_REPLIES = {
    "id": REMOTE_REPLIES_ID,
    "attributedTo": REMOTE_ID,
    "type": "Collection",
    "totalItems": 2,
    "items": [
        REPLY_2_ID,
        REPLY_4_ID,
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
    elif url == REPLIES_ID:
        return MagicMock(status_code=200, json=lambda: REPLIES)
    elif url == REPLY_1_ID:
        return MagicMock(status_code=200, json=lambda: REPLY_1)
    elif url == REPLY_2_ID:
        return MagicMock(status_code=200, json=lambda: REPLY_2)
    elif url == REPLY_3_ID:
        return MagicMock(status_code=200, json=lambda: REPLY_3)
    elif url == REPLY_4_ID:
        return MagicMock(status_code=200, json=lambda: REPLY_4)
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
        if data["id"] == REMOTE_REPLIES_ID:
            return MagicMock(status_code=200, json=lambda: REMOTE_REPLIES)
        if data["id"] == REPLY_5_ID:
            return MagicMock(status_code=200, json=lambda: REPLY_5)
        else:
            return MagicMock(status_code=404)
    else:
        return MagicMock(status_code=404)


class TestRepliesCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_replies_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["replies", OBJECT_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertIn(REPLY_1_ID, output)
        self.assertIn(REPLY_3_ID, output)
        self.assertIn(REPLY_5_ID, output)
        self.assertNotIn(REPLY_2_ID, output)
        self.assertNotIn(REPLY_4_ID, output)
        self.assertIn("another@social.example", output)
        self.assertIn(REPLY_3["contentMap"]["en"], output)

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_replies_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["replies", REMOTE_OBJECT_ID], {'LANG':  'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        output = sys.stdout.getvalue()
        self.assertNotIn(REPLY_1_ID, output)
        self.assertNotIn(REPLY_3_ID, output)
        self.assertNotIn(REPLY_5_ID, output)
        self.assertIn(REPLY_2_ID, output)
        self.assertIn(REPLY_4_ID, output)
        self.assertIn("andanother@social.example", output)
        self.assertIn(REPLY_4["contentMap"]["en"], output)


if __name__ == "__main__":
    unittest.main()
