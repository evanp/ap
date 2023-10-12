import requests
import webfinger

def to_id(prop):
    if isinstance(prop, dict):
        return prop['id']
    elif isinstance(prop, str):
        return prop
    else:
        raise Exception('Invalid property type')

def get_actor(id):
    if not id.startswith('https://'):
        wf = webfinger.finger(id)
        matches = [l['href'] for l in wf['links'] if l['rel'] == 'self' and l['type'] == 'application/activity+json']
        if len(matches) == 0:
            raise Exception('No ActivityPub account found')
        id = matches[0]
    headers = {
        'Accept': 'application/ld+json,application/activity+json,application/json'
    }
    r = requests.get(id, headers=headers)
    r.raise_for_status()
    return r.json()

def items(url):
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
        page_id = to_id(coll['first'])
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
                page_id = to_id(page['next'])
            else:
                page_id = None

if __name__ == '__main__':
    import sys
    from itertools import islice

    for item in islice(items(sys.argv[1]), 100):
        print(item)
