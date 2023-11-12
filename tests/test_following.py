import unittest
from unittest.mock import patch, mock_open, MagicMock
from commands.following import FollowingCommand
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json

ACTOR_ID = 'https://social.example/users/evanp'
OTHER_1_ID = 'https://different.example/users/other1'
OTHER_2_ID = 'https://social.example/users/other2'
FOLLOWING_ID = f'{ACTOR_ID}/followers'
PAGE_2_ID = f'{FOLLOWING_ID}/page/2'
PAGE_1_ID = f'{FOLLOWING_ID}/page/1'

ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": f'{ACTOR_ID}/outbox',
    "inbox": f'{ACTOR_ID}/outbox',
    "following": FOLLOWING_ID,
    "preferredUsername": 'evanp',
    "endpoints": {
        "proxyUrl": "https://social.example/proxy"
    }
}

OTHER_1 = {
    "type": "Person",
    "id": OTHER_1_ID,
    "outbox": f'{OTHER_1_ID}/outbox',
    "inbox": f'{OTHER_1_ID}/inbox',
    "preferredUsername": 'other1'
}

OTHER_2 = {
    "type": "Person",
    "id": OTHER_2_ID,
    "outbox": f'{OTHER_2_ID}/outbox',
    "inbox": f'{OTHER_2_ID}/inbox',
    "preferredUsername": 'other2'
}

FOLLOWING = {
    "id": FOLLOWING_ID,
    "attributedTo": ACTOR_ID,
    "first": PAGE_2_ID
}

PAGE_2 = {
    "id": PAGE_2_ID,
    "partOf": FOLLOWING_ID,
    "next": PAGE_1_ID,
    "orderedItems": [
        {
            "id": OTHER_1_ID,
            "type": "Person",
            "preferredUsername": "other1"
        }
    ]
}

PAGE_1 = {
    "id": PAGE_1_ID,
    "partOf": FOLLOWING_ID,
    "prev": PAGE_2_ID,
    "orderedItems": [
        {
            "id": OTHER_2_ID,
            "type": "Person",
            "preferredUsername": "other2"
        }
    ]
}

TOKEN_FILE_DATA = json.dumps({
    "actor_id": ACTOR_ID,
    "access_token": "12345678"
})

def mock_oauth_get(url, headers=None):
    if url == ACTOR_ID:
        return MagicMock(status_code=200, json=lambda: ACTOR)
    elif url == FOLLOWING_ID:
        return MagicMock(status_code=200, json=lambda: FOLLOWING)
    elif url == PAGE_2_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_2)
    elif url == PAGE_1_ID:
        return MagicMock(status_code=200, json=lambda: PAGE_1)
    elif url == OTHER_2_ID:
        return MagicMock(status_code=200, json=lambda: OTHER_2)
    else:
        return MagicMock(status_code=404)


def mock_oauth_post(url, headers=None, data=None):
    if url == ACTOR['endpoints']['proxyUrl']:
        if data['id'] == OTHER_1_ID:
            return MagicMock(status_code=200, json=lambda: OTHER_1)
        else:
            return MagicMock(status_code=404)
    else:
        return MagicMock(status_code=404)

class TestFollowingCommand(unittest.TestCase):

    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch('builtins.open', new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    @patch('requests_oauthlib.OAuth2Session.post', side_effect=mock_oauth_post)
    @patch('requests_oauthlib.OAuth2Session.get', side_effect=mock_oauth_get)
    def test_following(self, mock_requests_post, mock_requests_get, mock_file):
        args = Namespace(subcommand='following', limit=10, offset=0)
        cmd = FollowingCommand(args)

        cmd.run()

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        self.assertIn("other2@social.example", sys.stdout.getvalue())
        self.assertIn("other1@different.example", sys.stdout.getvalue())

if __name__ == '__main__':
    unittest.main()
