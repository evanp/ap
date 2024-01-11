import unittest
from unittest.mock import patch, mock_open, Mock
from ap.main import run_command
from argparse import Namespace
import io
import sys
import requests
from requests.models import Response
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = "https://social.example/users/evanp"
OTHER_ID = "https://different.example/users/other"
INBOX_ID = f"{ACTOR_ID}/inbox"
PAGE_2_ID = f"{INBOX_ID}/page/2"
PAGE_1_ID = f"{INBOX_ID}/page/1"
OTHER_ACTIVITY_ID = f"{OTHER_ID}/activity/11"
ACTIVITY_ID = f"{ACTOR_ID}/activity/10"
INBOX = {"id": INBOX_ID, "attributedTo": ACTOR_ID, "first": PAGE_2_ID}

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f"{ACTOR_ID}/outbox",
    "inbox": INBOX_ID,
    "preferredUsername": "evanp",
    "endpoints": {"proxyUrl": "https://social.example/proxy"},
}

OTHER = {
    "type": "Person",
    "id": OTHER_ID,
    "outbox": f"{OTHER_ID}/outbox",
    "inbox": f"{OTHER_ID}/inbox",
    "preferredUsername": "other",
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": INBOX_ID,
    "next": PAGE_1_ID,
    "orderedItems": [
        {
            "type": "Activity",
            "id": OTHER_ACTIVITY_ID,
            "summary": "Page 2 Activity 11",
        }
    ],
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": INBOX_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [
        {
            "type": "Activity",
            "id": ACTIVITY_ID,
            "summary": "Page 1 Activity 10",
        }
    ],
}

ACTIVITY = {
    "id": ACTIVITY_ID,
    "actor": ACTOR_ID,
    "type": "Activity",
    "summary": "Page 1 Activity 10",
    "published": "2021-01-01T00:00:00Z",
}

OTHER_ACTIVITY = {
    "actor": OTHER_ID,
    "type": "Activity",
    "id": f"{OTHER_ID}/activity/11",
    "summary": "Page 2 Activity 11",
    "published": "2021-01-01T00:00:00Z",
}

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})

def mock_response(url, obj):
    r = Response()
    r.url = url
    r.status_code = 200
    r.reason = "OK"
    r._content = json.dumps(obj).encode("utf-8")
    r.headers["Content-Type"] = "application/ld+json; profile=\"https://www.w3.org/ns/activitystreams\""
    return r

def mock_404(url):
    r = Response()
    r.status_code = 404
    r.url = url
    r.reason = "Not found"
    r._content = b"Not found"
    r.headers["Content-Type"] = "text/plain"
    return r

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return mock_response(ACTOR_ID, ACTOR)
    elif url == INBOX_ID:
        return mock_response(INBOX_ID, INBOX)
    elif url == PAGE_2_ID:
        return mock_response(PAGE_2_ID, PAGE_2)
    elif url == PAGE_1_ID:
        return mock_response(PAGE_1_ID, PAGE_1)
    elif url == ACTIVITY_ID:
        return mock_response(ACTIVITY_ID, ACTIVITY)
    else:
        return mock_404()


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR["endpoints"]["proxyUrl"]:
        if data["id"] == OTHER_ID:
            return mock_response(OTHER_ID, OTHER)
        elif data["id"] == OTHER_ACTIVITY_ID:
            return mock_response(OTHER_ACTIVITY_ID, OTHER_ACTIVITY)
        else:
            return mock_404(data["id"])
    else:
        return mock_404(url)


class TestInboxCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch("requests_oauthlib.OAuth2Session.post", side_effect=mock_oauth_post)
    @patch("requests_oauthlib.OAuth2Session.get", side_effect=mock_oauth_get)
    def test_inbox(self, mock_requests_post, mock_requests_get, mock_file):
        run_command(["inbox"], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn("Page 1 Activity 10", sys.stdout.getvalue())
        self.assertIn("evanp@social.example", sys.stdout.getvalue())
        self.assertIn("other@different.example", sys.stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
