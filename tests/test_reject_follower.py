import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.reject_follower import RejectFollowerCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = 'https://social.example/users/evanp'
OTHER_1_ID = 'https://different.example/users/other1'
OTHER_2_ID = 'https://social.example/users/other2'
REJECT_ID = f'{ACTOR_ID}/reject/1'
PENDING_FOLLOWERS_ID = f'{ACTOR_ID}/pending/followers'
PAGE_2_ID = f'{PENDING_FOLLOWERS_ID}/page/2'
PAGE_1_ID = f'{PENDING_FOLLOWERS_ID}/page/1'
FOLLOW_1_ID = f'{OTHER_1_ID}/follows/1'
FOLLOW_2_ID = f'{OTHER_2_ID}/follows/2'

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f'{ACTOR_ID}/outbox',
    "pendingFollowers": PENDING_FOLLOWERS_ID,
    "endpoints": {
        "proxyUrl": 'https://social.example/proxy'
    }
}

OTHER_1 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "preferredUsername": "other1",
    "inbox": f'{OTHER_1_ID}/inbox'
}

OTHER_2 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "preferredUsername": "other2",
    "inbox": f'{OTHER_2_ID}/inbox'
}


PENDING_FOLLOWERS = {
    "id": PENDING_FOLLOWERS_ID,
    "attributedTo": ACTOR_ID,
    "first": PAGE_2_ID
}

FOLLOW_1 = {
    "id": FOLLOW_1_ID,
    "actor": OTHER_1_ID,
    "type": "Follow",
    "object": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z"
}

FOLLOW_2 = {
    "id": FOLLOW_2_ID,
    "actor": OTHER_2_ID,
    "type": "Follow",
    "object": ACTOR_ID,
    "published": "2020-01-01T00:00:00Z"
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": PENDING_FOLLOWERS_ID,
    "next": PAGE_1_ID,
    "orderedItems": [
        FOLLOW_1
    ]
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": PENDING_FOLLOWERS_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [
        FOLLOW_2
    ]
}

TOKEN_FILE_DATA = json.dumps({
    "actor_id": "https://social.example/users/evanp",
    "access_token": "12345678"
})

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == PENDING_FOLLOWERS_ID:
        return MagicMock(status_code=200, json=lambda: PENDING_FOLLOWERS)
    elif url == PAGE_2_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_2)
    elif url == PAGE_1_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_1)
    elif url == OTHER_2_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_2)
    elif url == FOLLOW_2_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOW_2)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR['endpoints']['proxyUrl']:
        if data['id'] == OTHER_1_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_1)
        if data['id'] == FOLLOW_1_ID:
            return MagicMock(status_code=200, json=lambda: FOLLOW_1)
        else:
            return MagicMock(status_code=404)
    elif url == ACTOR['outbox']:
        added_data = {'id': REJECT_ID, 'published': '2020-01-01T00:00:00Z', 'actor': ACTOR_ID}
        return MagicMock(status_code=200, json=lambda: {**json.loads(data), **added_data})
    else:
        return MagicMock(status_code=404)

class TestRejectFollowerCommand(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch('builtins.open', new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch('requests_oauthlib.OAuth2Session.post', side_effect=mock_oauth_post)
    @patch('requests_oauthlib.OAuth2Session.get', side_effect=mock_oauth_get)
    def test_reject_follower_remote(self, mock_requests_get, mock_requests_post, mock_file):
        args = Namespace(subcommand='reject', subsubcommand='follower', id=OTHER_1_ID)
        cmd = RejectFollowerCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_1_ID, sys.stdout.getvalue())

    @patch('builtins.open', new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch('requests_oauthlib.OAuth2Session.post', side_effect=mock_oauth_post)
    @patch('requests_oauthlib.OAuth2Session.get', side_effect=mock_oauth_get)
    def test_reject_follower_local(self, mock_requests_get, mock_requests_post, mock_file):
        args = Namespace(subcommand='reject', subsubcommand='follower', id=OTHER_2_ID)
        cmd = RejectFollowerCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn(OTHER_2_ID, sys.stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
