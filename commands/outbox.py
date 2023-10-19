from .command import Command
import itertools
from tabulate import tabulate

class OutboxCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception('Not logged in')
        outbox = actor.get('outbox', None)
        if outbox is None:
            raise Exception('No outbox found')
        outbox_id = self.to_id(outbox)
        slice = itertools.islice(
            self.items(outbox_id),
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
