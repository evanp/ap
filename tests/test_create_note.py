import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.main import run_command
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json
import logging

ACTOR_ID = "https://social.example/users/evanp"
OTHER_ID = "https://social.example/users/other"
CREATE_ID = f"{ACTOR_ID}/create/1"
ORIGINAL_POST_ID = f"{OTHER_ID}/note/2"

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
    "url": "https://social.example/user/other",
    "preferredUsername": "other"
}

OTHER_WEBFINGER_ID = "other@social.example"
OTHER_WEBFINGER_JSON = {
    "subject": "acct:other@social.example",
    "links": [{"rel": "self",
               "type": "application/activity+json",
               "href": OTHER_ID}]
}

WEBFINGER_URL_BASE = "https://social.example/.well-known/webfinger"
OTHER_WEBFINGER_URL = WEBFINGER_URL_BASE + "?resource=acct%3Aother%40social.example"

ORIGINAL_POST = {
    "type": "Note",
    "id": ORIGINAL_POST_ID,
    "contentMap": {
        "en":  "What should we say to the world?"
    },
    "attributedTo": OTHER_ID,
    "published": "2020-01-01T00:00:00Z",
}

CONTENT = "Hello, world!"
AT_MENTION_CONTENT = f"Hello, @other@social.example"
AT_MENTION_LINK = f" <a href=\"{OTHER['url']}\">@other@social.example</a>"
HASHTAG_CONTENT = f"Hello, World! #greeting"
HASHTAG_LINK = f'<a href="https://tags.pub/greeting">#greeting</a>'
LINK_CONTENT = f"Hello, https://example.com"
LINK_LINK = f"<a href=\"https://example.com\">https://example.com</a>"
MARKUP_CONTENT = f"This > that & that < this"
MARKUP_HTML = f"This &gt; that &amp; that &lt; this"

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == OTHER_ID:
        return MagicMock(status_code=200, json=lambda: OTHER)
    elif url == ORIGINAL_POST_ID:
        return MagicMock(status_code=200, json=lambda: ORIGINAL_POST)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["outbox"]:
        added_data = {
            "id": CREATE_ID,
            "published": "2020-01-01T00:00:00Z",
            "actor": ACTOR_ID,
        }
        combined = {**json.loads(data), **added_data}
        return MagicMock(
            status_code=200, json=lambda: combined
        )
    else:
        return MagicMock(status_code=404)


def mock_requests_get(url, **kwargs):
    if url == WEBFINGER_URL_BASE:
        return MagicMock(
            status_code=200,
            headers={"Content-Type": "application/jrd+json"},
            json=lambda: OTHER_WEBFINGER_JSON,
        )
    else:
        return MagicMock(status_code=404)


class TestCreateNoteCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_public(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", "--public", CONTENT], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        self.assertIn(CONTENT, sys.stdout.getvalue())
        self.assertIn("Public", sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_followers_only(
        self, mock_oauth_get, mock_oauth_post, mock_file
    ):
        run_command(["create", "note", "--followers-only", CONTENT], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        self.assertIn(CONTENT, sys.stdout.getvalue())
        self.assertIn(ACTOR["followers"], sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_private(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", '--to', OTHER_ID, CONTENT], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        self.assertIn(CONTENT, sys.stdout.getvalue())
        self.assertIn(OTHER_ID, sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_reply(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", '--public', '--in-reply-to', ORIGINAL_POST_ID, CONTENT],
                    {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        self.assertIn(CONTENT, sys.stdout.getvalue())
        self.assertIn(ORIGINAL_POST_ID, sys.stdout.getvalue())

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    @patch("requests.get", side_effect=mock_requests_get)
    def test_create_note_at_mention(
        self, mock_requests_get, mock_oauth_get, mock_oauth_post, mock_file
    ):
        run_command(["create", "note", '--public', AT_MENTION_CONTENT],
                    {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        activity = json.loads(sys.stdout.getvalue())
        self.assertIsNotNone(activity["object"])
        object = activity["object"]
        self.assertIn(AT_MENTION_CONTENT, object["source"]["content"])
        self.assertIn(AT_MENTION_LINK, object["content"])
        self.assertEqual(len(object["tag"]), 1)
        self.assertEqual(object['tag'][0]['type'], 'Mention')
        self.assertEqual(object['tag'][0]['href'], OTHER['url'])
        self.assertEqual(object['tag'][0]['name'], '@other@social.example')

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_hashtag(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", '--public', HASHTAG_CONTENT],
                    {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        activity = json.loads(sys.stdout.getvalue())
        self.assertIsNotNone(activity["object"])
        object = activity["object"]
        self.assertIn(HASHTAG_CONTENT, object["source"]["content"])
        self.assertIn(HASHTAG_LINK, object["content"])
        self.assertEqual(len(object["tag"]), 1)
        self.assertEqual(object['tag'][0]['type'], 'Hashtag')
        self.assertEqual(object["tag"][0]["href"], "https://tags.pub/greeting")
        self.assertEqual(object["tag"][0]["name"], "#greeting")

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_link(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", '--public', LINK_CONTENT],
                    {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        activity = json.loads(sys.stdout.getvalue())
        self.assertIsNotNone(activity["object"])
        object = activity["object"]
        self.assertIn(LINK_CONTENT, object["source"]["content"])
        self.assertIn(LINK_LINK, object["content"])

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_create_note_escape(self, mock_oauth_get, mock_oauth_post, mock_file):
        run_command(["create", "note", '--public', MARKUP_CONTENT],
                    {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_oauth_get.call_count, 1)
        self.assertGreaterEqual(mock_oauth_post.call_count, 1)
        activity = json.loads(sys.stdout.getvalue())
        self.assertIsNotNone(activity["object"])
        object = activity["object"]
        self.assertIn(MARKUP_CONTENT, object["source"]["content"])
        self.assertIn(MARKUP_HTML, object["content"])


if __name__ == "__main__":
    unittest.main()
