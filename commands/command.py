import requests
import webfinger
from pathlib import Path
import json
from requests_oauthlib import OAuth2Session

class Command:

    def __init__(self, args):
        self.args = args
        self._logged_in_actor = None
        self._logged_in_actor_id = None
        self._token_file_data = None
        self._session = None

    def logged_in_actor_id(self):
        if self._logged_in_actor_id is None:
            token = self.token_file_data()
            self._logged_in_actor_id = token.get('actor_id', None)
            if self._logged_in_actor_id is None:
                raise Exception('Not logged in')
        return self._logged_in_actor_id

    def token_file_data(self):
        if self._token_file_data is None:
            token_file = Path.home() / '.ap' / 'token.json'
            with open(token_file, 'r') as f:
                self._token_file_data = json.loads(f.read())
        return self._token_file_data

    def logged_in_actor(self):
        if self._logged_in_actor is None:
            id = self.logged_in_actor_id()
            oauth = self.session()
            r = oauth.get(id)
            r.raise_for_status()
            self._logged_in_actor = r.json()
        return self._logged_in_actor

    def session(self):
        if self._session is None:
            token = self.token_file_data()
            self._session = OAuth2Session(token=token)
        return self._session

    def to_id(self, prop):
        if isinstance(prop, dict):
            return prop['id']
        elif isinstance(prop, str):
            return prop
        else:
            raise Exception('Invalid property type')

    def get_actor_id(self, id):
        if not id.startswith('https://'):
            if id.startswith('@'):
                id = "acct:" + id[1:]
            elif id.startswith('acct:'):
                pass
            else:
                id = "acct:" + id
            wf = webfinger.finger(id)
            matches = [l['href'] for l in wf.links if l['rel'] == 'self' and l['type'] == 'application/activity+json']
            if len(matches) == 0:
                raise Exception('No ActivityPub account found')
            id = matches[0]
        return id

    def get_public(self, id):
        headers = {
            'Accept': 'application/ld+json,application/activity+json,application/json'
        }
        r = requests.get(id, headers=headers)
        r.raise_for_status()
        return r.json()

    def items(self, url):
        headers = {
            'Accept': 'application/ld+json,application/activity+json,application/json'
        }
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        coll = r.json()
        if coll.get('items', None) is not None:
            for item in coll['items']:
                yield item
            return
        elif coll.get('orderedItems', None) is not None:
            for item in coll['orderedItems']:
                yield item
            return
        elif coll.get('first', None) is not None:
            page_id = self.to_id(coll['first'])
            while page_id is not None:
                r = requests.get(page_id,headers=headers)
                r.raise_for_status()
                page = r.json()
                if page.get('items', None) is not None:
                    for item in page['items']:
                        yield item
                elif page.get('orderedItems', None) is not None:
                    for item in page['orderedItems']:
                        yield item
                else:
                    raise Exception('No items found in page')
                if page.get('next', None) is not None:
                    page_id = self.to_id(page['next'])
                else:
                    page_id = None
