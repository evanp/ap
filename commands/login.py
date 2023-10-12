from ..utils import get_actor
import webbrowser
import os
import base64
import hashlib
from pathlib import Path
from requests_oauthlib import OAuth2Session
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib

CLIENT_ID = 'https://evanp.github.io/ap/client.jsonld'
REDIRECT_URI = 'http://localhost:63546/redirect'
SCOPE = 'read write'

oauth = None
token_endpoint = None
state = None
verifier = None
server = None
token = None

class RedirectHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        global oauth, token_endpoint, state, verifier, code
        if self.path.startswith('/redirect'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Success</title></head><body><p>You may now close this window.</p></body></html>')
            self.wfile.close()
            qs = urllib.parse.parse_qs(self.path)
            if (state != qs['state'][0]):
                raise Exception('State mismatch')
            if (qs['error']):
                error = qs['error'][0]
                if (error == 'access_denied'):
                    print('Access denied')
                else:
                    print(f'Error: {error}')
                return
            code = qs['code'][0]
            token = oauth.fetch_token(token_endpoint, code=code, code_verifier=verifier)
            save_token(token)

def pkce():
    """Generate a PKCE code verifier and challenge

    Returns:
        tuple: A tuple containing the code verifier and challenge
    """
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
    challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')
    return (verifier, challenge)

def oauth_endpoints(json):
    if not json.has_key('endpoints'):
        raise Exception('No endpoints found')
    if not json['endpoints'].has_key('oauthAuthorizationEndpoint'):
        raise Exception('No oauthAuthorizationEndpoint found')
    if not json['endpoints'].has_key('oauthTokenEndpoint'):
        raise Exception('No oauthTokenEndpoint found')
    auth_endpoint = json['endpoints']['oauthAuthorizationEndpoint']
    token_endpoint = json['endpoints']['oauthTokenEndpoint']
    return (auth_endpoint, token_endpoint)

def save_token(token):
    apdir = Path.home() / '.ap'
    if not apdir.exists():
        apdir.mkdir(700)
    with open(apdir / 'token.json', 'w') as f:
        f.write(json.dumps(token))

def login(id):
    """Log into an ActivityPub server

    Args:
        id (str): The ID of the user to login as; either an
            ActivityPub ID or a webfinger address
    """

    global oauth, token_endpoint, state, verifier, code

    json = get_actor(id)

    (auth_endpoint, token_endpoint) = oauth_endpoints(json)

    (verifier, challenge) = pkce()

    oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
    authorization_url, state = oauth.authorization_url(auth_endpoint, code_challenge=challenge, code_challenge_method='S256')

    webbrowser.open(authorization_url)

    # Processing continues in RedirectHandler.do_GET!

    server = HTTPServer(('localhost', 63546), RedirectHandler)
    server.handle_request()  # To handle only the first request
    server.server_close()