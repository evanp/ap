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
            activity = self.to_object(item, ['id', 'actor', 'published'])
            follower = self.to_object(
                activity['actor'],
                [ 'id',
                  'preferredUsername',
                  ['name', 'nameMap', 'summary', 'summaryMap'] ]
            )
            activity_id = self.to_id(activity)
            id = self.to_webfinger(follower)
            name = self.to_text(follower)
            published = activity['published'] if 'published' in activity else None
            rows.append([activity_id, id, name, published])
        print(tabulate(rows, headers=['activity', 'id', 'name', 'published']))
