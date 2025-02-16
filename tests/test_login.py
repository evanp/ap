import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.main import run_command
from argparse import Namespace
import io
import sys
import requests
from requests_oauthlib import OAuth2Session
import json
from ap.version import __version__
import logging
import webbrowser
import threading
import time
import urllib.request
from urllib.parse import urlparse, parse_qs, urlencode
from pathlib import Path

USER_AGENT = f"ap/{__version__}"

AUTHORIZATION_ENDPOINT = "https://social.example/oauth/authorization"
TOKEN_ENDPOINT = "https://social.example/oauth/token"

ACTOR_ID = "https://social.example/users/evanp"
ACTOR = {
    "type": "Person",
    "id": ACTOR_ID,
    "outbox": "https://social.example/users/evanp/outbox",
    "endpoints": {
        "oauthAuthorizationEndpoint": AUTHORIZATION_ENDPOINT,
        "oauthTokenEndpoint": TOKEN_ENDPOINT
    }
}

ACTOR_WEBFINGER_ID = "evanp@social.example"

WEBFINGER_URL_BASE = "https://social.example/.well-known/webfinger"
ACTOR_WEBFINGER_URL = WEBFINGER_URL_BASE + "?resource=acct%3Aevanp%40social.example"

ACTOR_WEBFINGER_JSON = {
    "subject": "acct:evanp@social.example",
    "links": [{"rel": "self",
               "type": "application/activity+json",
               "href": ACTOR_ID}]
}

AUTHORIZATION_CODE = '1234567890ABCDEF'
ACCESS_TOKEN = {
    "access_token": 'XYZPDQ',
    "token_type": 'Bearer',
    "scope": 'read write',
    "expires_in": 86400,
    "refresh_token": 'OMGBBQ'
}

def mock_requests_get(url, **kwargs):
    if url == WEBFINGER_URL_BASE:
        return MagicMock(
            status_code=200,
            headers={"Content-Type": "application/jrd+json"},
            json=lambda: ACTOR_WEBFINGER_JSON,
        )
    elif url == ACTOR_ID:
        return MagicMock(status_code=200,
                         headers={"Content-Type": "application/activity+json"},
                         json=lambda: ACTOR
                         )
    else:
        return MagicMock(status_code=404)

def mock_oauth_request(url, **kwargs):
    if url == TOKEN_ENDPOINT:
        return MagicMock(
            status_code=200,
            headers={"Content-Type": "application/json"},
            text=json.dumps(ACCESS_TOKEN)
        )
    else:
        return MagicMock(status_code=404)

authorization_params = None
web_response = None

def mock_webbrowser_open(url):
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if base_url == AUTHORIZATION_ENDPOINT:
        global authorization_params
        authorization_params = parse_qs(parsed.query)
        redirect_uri = authorization_params["redirect_uri"][0]
        def delayed_callback():
            time.sleep(0.1)
            params = {
                "code": AUTHORIZATION_CODE,
                "state": authorization_params['state'][0]
            }
            uri = redirect_uri + "?" + urlencode(params)
            with urllib.request.urlopen(uri) as response:
                global web_response
                web_response = response.read()
        threading.Thread(target=delayed_callback).start()

class TestLoginCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch.object(Path, 'mkdir')
    @patch("builtins.open", new_callable=mock_open)
    @patch('webbrowser.open', side_effect=mock_webbrowser_open)
    @patch('requests.get', side_effect=mock_requests_get)
    @patch("requests_oauthlib.OAuth2Session.request", side_effect=mock_oauth_request)
    def test_login(self, mock_requests_post, mock_requests_get, mock_webbrowser_open, mock_file, mock_path_mkdir):
        run_command(["login", ACTOR_WEBFINGER_ID], {'LANG': 'en_CA.UTF-8', 'HOME': '/home/notauser'})

        # Assertions
        self.assertGreaterEqual(mock_requests_get.call_count, 1)
        self.assertGreaterEqual(mock_requests_post.call_count, 1)
        mock_webbrowser_open.assert_called_once()

        global authorization_params
        assert "client_id" in authorization_params

        mock_file.assert_called_once_with(Path('/home/notauser/.ap/token.json'), 'w')
