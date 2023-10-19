from .command import Command
import json
import itertools
from tabulate import tabulate

class InboxCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception('Not logged in')
        inbox = actor.get('inbox', None)
        if inbox is None:
            raise Exception('No inbox found')
        inbox_id = self.to_id(inbox)
        slice = itertools.islice(
            self.items(inbox_id),
            self.offset,
            self.offset + self.limit
        )
        rows = []
        for item in slice:
            id = self.to_id(item)
            actor = self.to_webfinger(item['actor'], ['id', 'preferredUsername'])
            type = item.get('type', None)
            summary = self.text_prop(item, 'summary')
            published = item.get('published')
            rows.append([id, actor, type, summary, published])
        tabulate(rows, headers=['id', 'actor', 'type', 'summary', 'published'])
