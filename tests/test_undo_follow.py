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
OTHER_3_ID = "https://different.example/users/other3"
OTHER_4_ID = "https://social.example/users/other4"
PENDING_FOLLOWING_ID = f"{ACTOR_ID}/following/pending"
FOLLOWING_ID = f"{ACTOR_ID}/following"
PENDING_FOLLOWING_PAGE_ID = f"{PENDING_FOLLOWING_ID}/page/1"
FOLLOWING_PAGE_ID = f"{FOLLOWING_ID}/page/1"
FOLLOW_1_ID = f"{ACTOR_ID}/follows/1"
FOLLOW_2_ID = f"{ACTOR_ID}/follows/2"
FOLLOW_3_ID = f"{ACTOR_ID}/follows/3"
FOLLOW_4_ID = f"{ACTOR_ID}/follows/4"
OUTBOX_ID = f"{ACTOR_ID}/outbox"
OUTBOX_PAGE_ID = f"{OUTBOX_ID}/page/1"
UNDO_ID = f"{ACTOR_ID}/undo/1"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": OUTBOX_ID,
    "inbox": f"{ACTOR_ID}/inbox",
    "pendingFollowing": PENDING_FOLLOWING_ID,
    "following": FOLLOWING_ID,
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

OTHER_3 = {
    "type": "Person",
    "id": OTHER_3_ID,
    "outbox": f"{OTHER_1_ID}/outbox",
    "inbox": f"{OTHER_1_ID}/inbox",
    "preferredUsername": "other3",
}

OTHER_4 = {
    "type": "Person",
    "id": OTHER_4_ID,
    "outbox": f"{OTHER_2_ID}/outbox",
    "inbox": f"{OTHER_2_ID}/inbox",
    "preferredUsername": "other4",
}

FOLLOW_1 = {
    "id": FOLLOW_1_ID,
    "actor": ACTOR_ID,
    "type": "Follow",
    "object": OTHER_1_ID,
    "published": "2020-01-01T00:00:00Z",
}

FOLLOW_2 = {
    "id": FOLLOW_2_ID,
    "actor": ACTOR_ID,
    "type": "Follow",
    "object": OTHER_2_ID,
    "published": "2020-01-01T00:00:00Z",
}

FOLLOW_3 = {
    "id": FOLLOW_3_ID,
    "actor": ACTOR_ID,
    "type": "Follow",
    "object": OTHER_3_ID,
    "published": "2020-01-01T00:00:00Z",
}

FOLLOW_4 = {
    "id": FOLLOW_4_ID,
    "actor": ACTOR_ID,
    "type": "Follow",
    "object": OTHER_4_ID,
    "published": "2020-01-01T00:00:00Z",
}

PENDING_FOLLOWING = {
    "id": PENDING_FOLLOWING_ID,
    "attributedTo": ACTOR_ID,
    "first": PENDING_FOLLOWING_PAGE_ID,
}

PENDING_FOLLOWING_PAGE = {
    "id": PENDING_FOLLOWING_PAGE_ID,
    "attributedTo": ACTOR_ID,
    "partOf": PENDING_FOLLOWING_ID,
    "orderedItems": [FOLLOW_1, FOLLOW_2],
}

FOLLOWING = {
    "id": FOLLOWING_ID,
    "attributedTo": ACTOR_ID,
    "first": FOLLOWING_PAGE_ID,
}

FOLLOWING_PAGE = {
    "id": FOLLOWING_PAGE_ID,
    "attributedTo": ACTOR_ID,
    "partOf": FOLLOWING_ID,
    "orderedItems": [OTHER_3, OTHER_4],
}

OUTBOX = {
    "id": OUTBOX_ID,
    "attributedTo": ACTOR_ID,
    "first": OUTBOX_PAGE_ID
}

OUTBOX_PAGE = {
    "id": OUTBOX_PAGE_ID,
    "attributedTo": ACTOR_ID,
    "partOf": OUTBOX_ID,
    "orderedItems": [FOLLOW_3, FOLLOW_4],
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == PENDING_FOLLOWING_ID:
        return MagicMock(status_code=200, json=lambda: PENDING_FOLLOWING)
    elif url == FOLLOWING_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOWING)
    elif url == PENDING_FOLLOWING_PAGE_ID:
        return MagicMock(status_code=200, json=lambda: PENDING_FOLLOWING_PAGE)
    elif url == FOLLOWING_PAGE_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOWING_PAGE)
    elif url == OUTBOX_ID:
        return MagicMock(status_code=200, json=lambda: OUTBOX)
    elif url == OUTBOX_PAGE_ID:
        return MagicMock(status_code=200, json=lambda: OUTBOX_PAGE)
    elif url == OTHER_2_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_2)
    elif url == OTHER_4_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_4)
    elif url == FOLLOW_1_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_1)
    elif url == FOLLOW_2_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_2)
    elif url == FOLLOW_3_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_3)
    elif url == FOLLOW_4_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_4)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == OTHER_1_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_1)
        if data["id"] == OTHER_3_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_3)
        else:
            return MagicMock(status_code=404)
    elif url == OUTBOX_ID:
        new_data = {
            **json.loads(data),
            "id": UNDO_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID}
        return MagicMock(status_code=201, json=lambda: new_data)
    else:
        return MagicMock(status_code=404)


class TestUndoFollowCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_undo_follow_pending_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["undo", "follow", OTHER_1_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_1_ID, sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_undo_follow_pending_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["undo", "follow", OTHER_2_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_2_ID, sys.stdout.getvalue())


    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_undo_follow_remote(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["undo", "follow", OTHER_3_ID], {})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_3_ID, sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_undo_follow_local(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["undo", "follow", OTHER_4_ID], {})


        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_4_ID, sys.stdout.getvalue())

if __name__ == "__main__":
    unittest.main()
