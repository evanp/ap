import requests
import webfinger

class Command:

    def __init__(self, args):
        self.args = args

    def to_id(self, prop):
        if isinstance(prop, dict):
            return prop['id']
        elif isinstance(prop, str):
            return prop
        else:
            raise Exception('Invalid property type')

    def get_actor(self, id):
        if not id.startswith('https://'):
            if id.startswith('@'):
                id = "acct:" + id[1:]
            elif id.startswith('acct:'):
                pass
            else:
                id = "acct:" + id
            wf = webfinger.finger(id)
            print(wf.links)
            matches = [l['href'] for l in wf.links if l['rel'] == 'self' and l['type'] == 'application/activity+json']
            if len(matches) == 0:
                raise Exception('No ActivityPub account found')
            id = matches[0]
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
