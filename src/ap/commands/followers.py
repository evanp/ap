from .command import Command
from tabulate import tabulate
from requests.exceptions import RequestException

class FollowersCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.offset = args.offset
        self.limit = args.limit

    def run(self):
        coll = self.get_actor_collection("followers")
        slice = self.collection_slice(coll, self.offset, self.limit)
        rows = []
        for item in slice:
            try:
                follower = self.to_object(
                    item,
                    [
                        "id",
                        "preferredUsername",
                        ["name", "nameMap", "summary", "summaryMap"],
                    ],
                )
                id = self.to_webfinger(follower)
                name = self.to_text(follower)
                rows.append([id, name])
            except RequestException as e:
                rows.append(['<unavailable>', self.to_id(item)])

        print(tabulate(rows, headers=["id", "name"]))
