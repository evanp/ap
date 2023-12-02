from .command import Command
from tabulate import tabulate
import json

class RepliesCommand(Command):
    """`replies` command"""

    def __init__(self, args, env):
        super().__init__(args, env)
        self.id = args.id
        self.limit = args.limit
        self.offset = args.offset

    def run(self):
        """Run the command"""

        obj = self.get_object(self.id)
        if obj is None:
            raise ValueError("Object not found")

        if "replies" not in obj:
            raise ValueError("Object has no replies")

        replies_id = self.to_id(obj["replies"])

        replies_slice = self.collection_slice(replies_id, self.offset, self.limit)

        rows = []

        for item in replies_slice:
            id = self.to_id(item)
            reply = self.to_object(item,
                                      ["attributedTo",
                                       "published",
                                       ["content", "contentMap"]])
            if "contentMap" not in reply:
                raise Exception(f'No contentMap in {id}')
            attributedTo = self.to_webfinger(reply["attributedTo"])
            published = reply.get("published")
            content = self.text_prop(reply, "content")
            if content is None:
                raise Exception(f'No content in {id}')
            rows.append([id, attributedTo, content, published])

        print(tabulate(rows, headers=["id", "attributedTo", "content", "published"]))
