from .command import Command
import itertools
from tabulate import tabulate

class FollowersCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception('Not logged in')
        followers = actor.get('followers', None)
        if followers is None:
            raise Exception('No followers found')
        followers_id = self.to_id(followers)
        slice = itertools.islice(
            self.items(followers_id),
            self.offset,
            self.offset + self.limit
        )
        rows = []
        for item in slice:
            follower = self.to_object(
                item['object'],
                [ 'id',
                  'preferredUsername',
                  ['name', 'nameMap', 'summary', 'summaryMap'] ]
            )
            id = self.to_webfinger(follower)
            name = self.to_text(follower)
            rows.append([id, name])
        print(tabulate(rows, headers=['id', 'name']))
