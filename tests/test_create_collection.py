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
CREATE_ID = f"{ACTOR_ID}/create/1"
NAME = "Photos from Bali"
COLLECTION_ID = f"{ACTOR_ID}/collections/1"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "followers": f"{ACTOR_ID}/followers",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER = {
    "type": "Person",
    "id": OTHER_ID,
    "outbox": f"{OTHER_ID}/outbox",
    "followers": f"{OTHER_ID}/followers",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})


def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == OTHER_ID:
        return MagicMock(status_code=200, json=lambda: OTHER)
    else:
        return MagicMock(status_code=404)

posted = []

def mock_oauth_post(url, headers=None, data=None):
    global posted
    if url == ACTOR["outbox"]:
        input_data = json.loads(data)
        posted.append(input_data)
        input_object = input_data["object"]
        added_object = {'id': COLLECTION_ID}
        added_data = {
            "id": CREATE_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID,
            "object": {**input_object, **added_object}
        }
        return MagicMock(
            status_code=200, json=lambda: {**input_data, **added_data}
        )
    else:
        return MagicMock(status_code=404)


class TestCreateCollectionCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_collection_public(self, mock_requests_get, mock_requests_post, mock_file):
        global posted

        posted = []
        run_command(["create", "collection", "--public", NAME], {"LANG": "en_US.UTF-8", 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(NAME, sys.stdout.getvalue())
        self.assertIn("Public", sys.stdout.getvalue())
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["to"], ["https://www.w3.org/ns/activitystreams#Public"])
        self.assertEqual(posted[0]["object"]["type"], "Collection")

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_collection_followers_only(
        self, mock_requests_get, mock_requests_post, mock_file
    ):
        global posted
        posted = []
        run_command(["create", "collection", "--followers-only", NAME], {"LANG": "en_US.UTF-8", 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(NAME, sys.stdout.getvalue())
        self.assertIn(ACTOR["followers"], sys.stdout.getvalue())
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["to"], [ACTOR["followers"]])
        self.assertEqual(posted[0]["object"]["type"], "Collection")

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_collection_private(
        self, mock_requests_get, mock_requests_post, mock_file
    ):
        global posted
        posted = []

        run_command(["create", "collection", '--to', OTHER_ID, NAME], {"LANG": "en_US.UTF-8", 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(NAME, sys.stdout.getvalue())
        self.assertIn(OTHER_ID, sys.stdout.getvalue())
        self.assertEqual(len(posted), 1)
        self.assertEqual(posted[0]["to"], [OTHER_ID])
        self.assertEqual(posted[0]["object"]["type"], "Collection")


if __name__ == "__main__":
    unittest.main()
