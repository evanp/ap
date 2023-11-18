import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.update_note import UpdateNoteCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json
import ap

ACTOR_ID = "https://social.example/users/evanp"
UPDATE_ID = f"{ACTOR_ID}/update/1"
NOTE_ID = f"{ACTOR_ID}/notes/1"
CONTENT = "Hello, world!"
NEW_CONTENT = "Hello, world! (updated)"
FOLLOWERS_ID = f"{ACTOR_ID}/followers"

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "followers": FOLLOWERS_ID,
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

ORIGINAL_NOTE = {
    "type": "Note",
    "id": NOTE_ID,
    "content": CONTENT,
    "attributedTo": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
    "updated": "2020-01-01T00:00:00Z",
    "to": [FOLLOWERS_ID],
}

NEW_NOTE = {
    "type": "Note",
    "id": NOTE_ID,
    "content": NEW_CONTENT,
    "attributedTo": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z",
    "updated": "2020-01-01T00:01:00Z",
    "to": [FOLLOWERS_ID],
}

TOKEN_FILE_DATA = json.dumps({
    "actor_id": ACTOR_ID,
    "access_token": "12345678"
})

updated = False

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == NOTE_ID:
        if updated:
            return MagicMock(status_code=200, json=lambda: NEW_NOTE)
        else:
            return MagicMock(status_code=200, json=lambda: ORIGINAL_NOTE)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["outbox"]:
        updated = True
        added_data = {
            "id": UPDATE_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID,
            "object": NEW_NOTE,
        }
        return MagicMock(
            status_code=200, json=lambda: {**json.loads(data), **added_data}
        )
    else:
        return MagicMock(status_code=404)


class TestUpdateNoteCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_update_note(self, mock_requests_get, mock_requests_post, mock_file):
        args = Namespace(
            subcommand="update",
            subsubcommand="note",
            id=NOTE_ID,
            content=[NEW_CONTENT],
        )
        cmd = UpdateNoteCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(NEW_CONTENT, sys.stdout.getvalue())
        self.assertIn(NEW_NOTE['updated'], sys.stdout.getvalue())
        self.assertIn(UPDATE_ID, sys.stdout.getvalue())