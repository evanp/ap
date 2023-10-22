import requests
import webfinger
from pathlib import Path
import json
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse
import locale

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

    def to_object(self, obj, required=[]):
        if isinstance(obj, dict):
            if all(r in obj for r in required if isinstance(r, str)) and all(any(opt in obj for opt in r) for r in required if isinstance(r, list)):
                return obj
            elif 'id' in obj:
                return self.get_object(obj['id'])
            else:
                raise Exception('Cannot satisfy requirements')
        elif isinstance(obj, str):
            return self.get_object(obj)
        else:
            raise Exception('Invalid property type')

    def to_webfinger(self, obj):
        obj = self.to_object(obj, ['id', 'preferredUsername'])
        if 'id' not in obj or 'preferredUsername' not in obj:
            raise Exception('Cannot format this as a webfinger')
        return obj['preferredUsername'] + '@' + urlparse(obj['id']).netloc

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

    def get_object(self, id):
        actor_id = self.logged_in_actor_id()
        if actor_id is None:
            raise Exception('Not logged in')
        if (urlparse(id).netloc == urlparse(actor_id).netloc):
            data = self.get_local(id)
        else:
            data = self.get_by_proxy(id)
        return data

    def get_local(self, id):
        oauth = self.session()
        headers = {
            'Accept': 'application/ld+json,application/activity+json,application/json'
        }
        r = oauth.get(id, headers=headers)
        r.raise_for_status()
        return r.json()

    def get_by_proxy(self, id):
        actor = self.logged_in_actor()
        endpoints = actor.get('endpoints', None)
        if (endpoints is None):
            raise Exception('No endpoints found')
        proxyUrl = endpoints.get('proxyUrl', None)
        if (proxyUrl is None):
            raise Exception('No proxyUrl found')
        oauth = self.session()
        r = oauth.post(proxyUrl, data={'id': id})
        r.raise_for_status()
        return r.json()

    def items(self, url):
        coll = self.get_object(url)
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
                page = self.get_object(page_id)
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

    def do_activity(self, act):
        actor = self.logged_in_actor()
        if 'outbox' not in actor:
            raise Exception('No outbox found')
        outbox_id = self.to_id(actor['outbox'])
        oauth = self.session()
        headers = {
            'Content-Type': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
        }
        data = {'@context': 'https://www.w3.org/ns/activitystreams',
                **act}
        r = oauth.post(outbox_id, headers=headers, data=json.dumps(data))
        r.raise_for_status()
        return r.json()

    def text_prop(self, obj, name):
        if name in obj:
            return obj[name]
        elif name + 'Map' in obj:
            m = obj[name + 'Map']
            current_locale, encoding = locale.getdefaultlocale()
            language_code = current_locale[:2]
            if language_code in m:
                return m[language_code]
            elif 'unk' in m:
                return m['unk']
            else:
                return None
        else:
            return None

    def to_text(self, obj):
        text = self.text_prop(obj, 'name')
        if text is None:
            text = self.text_prop(obj, 'summary')
        return text