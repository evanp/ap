from .command import Command
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
REDIRECT_URI = 'http://localhost:63546/callback'
SCOPE = 'read write'

class LoginRedirectHandler(BaseHTTPRequestHandler):

    command = None

    def do_GET(self):
        global oauth, token_endpoint, state, verifier, code
        if self.path.startswith('/callback'):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><head><title>Success</title></head><body><p>You may now close this window.</p></body></html>')
            self.wfile.close()
            LoginRedirectHandler.command.on_callback(urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query))

class LoginCommand(Command):


    def __init__(self, args):
        super().__init__(args)
        self.id = args.id
        print(self.id)

    def pkce(self):
        """Generate a PKCE code verifier and challenge

        Returns:
            tuple: A tuple containing the code verifier and challenge
        """
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
        challenge = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')
        return (verifier, challenge)

    def oauth_endpoints(self, json):
        endpoints = json.get('endpoints', None)
        if endpoints is None:
            raise Exception('No endpoints found')
        auth_endpoint = endpoints.get('oauthAuthorizationEndpoint', None)
        if auth_endpoint is None:
            raise Exception('No oauthAuthorizationEndpoint found')
        token_endpoint = endpoints.get('oauthTokenEndpoint', None)
        if token_endpoint is None:
            raise Exception('No oauthTokenEndpoint found')
        return (auth_endpoint, token_endpoint)

    def save_token(self, token):
        apdir = Path.home() / '.ap'
        if not apdir.exists():
            apdir.mkdir(700)
        with open(apdir / 'token.json', 'w') as f:
            f.write(json.dumps(token))

    def run(self):
        """Log into an ActivityPub server

        Args:
            id (str): The ID of the user to login as; either an
                ActivityPub ID or a webfinger address
        """

        json = self.get_actor(self.id)

        (auth_endpoint, token_endpoint) = self.oauth_endpoints(json)

        self.token_endpoint = token_endpoint

        (verifier, challenge) = self.pkce()

        self.verifier = verifier

        self.oauth = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=SCOPE)
        authorization_url, state = self.oauth.authorization_url(auth_endpoint, code_challenge=challenge, code_challenge_method='S256')

        self.state = state

        webbrowser.open(authorization_url)

        # Processing continues in on_callback()

        LoginRedirectHandler.command = self

        server = HTTPServer(('localhost', 63546), LoginRedirectHandler)
        server.handle_request()  # To handle only the first request
        server.server_close()

    def on_callback(self, qs):
        if (self.state != qs['state'][0]):
               raise Exception('State mismatch')
        if (qs['error']):
            error = qs['error'][0]
            if (error == 'access_denied'):
                print('Access denied')
            else:
                print(f'Error: {error}')
                return
        code = qs['code'][0]
        token = self.oauth.fetch_token(self.token_endpoint, code=code, code_verifier=self.verifier)
        self.save_token(token)
