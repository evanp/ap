from .command import Command
from urllib.parse import urlparse
import json

class GetCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

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

    def run(self):
        actor_id = self.logged_in_actor_id()
        if actor_id is None:
            raise Exception('Not logged in')
        if (urlparse(self.id).netloc == urlparse(actor_id).netloc):
            data = self.get_local(self.id)
        else:
            data = self.get_by_proxy(self.id)
        print(json.dumps(data, indent=4))