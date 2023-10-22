from .command import Command
import itertools
from tabulate import tabulate

class FollowersCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        coll = self.get_actor_collection('followers')
        slice = self.collection_slice(coll, self.offset, self.limit)
        rows = []
        for item in slice:
            follower = self.to_object(
                item,
                [ 'id',
                  'preferredUsername',
                  ['name', 'nameMap', 'summary', 'summaryMap'] ]
            )
            id = self.to_webfinger(follower)
            name = self.to_text(follower)
            rows.append([id, name])
        print(tabulate(rows, headers=['id', 'name']))
