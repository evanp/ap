from .command import Command
import itertools
from tabulate import tabulate

class FollowingCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception('Not logged in')
        following = actor.get('following', None)
        if following is None:
            raise Exception('No following found')
        following_id = self.to_id(following)
        slice = itertools.islice(
            self.items(following_id),
            self.offset,
            self.offset + self.limit
        )
        rows = []
        for item in slice:
            activity = self.to_object(item, ['object'])
            followed = self.to_object(
                activity['object'],
                [ 'id',
                  'preferredUsername',
                  ['name', 'nameMap', 'summary', 'summaryMap'] ]
            )
            id = self.to_webfinger(followed)
            name = self.to_text(followed)
            rows.append([id, name])
        print(tabulate(rows, headers=['id', 'name']))
