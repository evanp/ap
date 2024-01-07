from .command import Command
import itertools
from tabulate import tabulate
from requests.exceptions import HTTPError

class InboxCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception("Not logged in")
        inbox = actor.get("inbox", None)
        if inbox is None:
            raise Exception("No inbox found")
        inbox_id = self.to_id(inbox)
        slice = itertools.islice(
            self.items(inbox_id), self.offset, self.offset + self.limit
        )
        rows = []
        for item in slice:
            # Use the object as provided as fallback
            try:
                object = self.to_object(item, ["actor", "type", "summary", "published"])
            except HTTPError as e:
                object = item
            id = self.to_id(object)
            type = object.get("type", None)
            summary = self.text_prop(object, "summary")
            published = object.get("published", None)
            # Use the actor id as fallback
            try:
                actor = self.to_webfinger(object["actor"])
            except HTTPError as e:
                actor = self.to_id(object["actor"])
            rows.append([id, actor, type, summary, published])
        print(tabulate(rows, headers=["id", "actor", "type", "summary", "published"]))
