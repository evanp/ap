from .command import Command
import json

class CreateCollectionCommand(Command):
    """Create a new collection"""

    def __init__(self, args, env):
        super().__init__(args, env)
        self.name = args.name
        self.public = args.public
        self.followers_only = args.followers_only
        self.private = args.private
        self.to = args.to
        self.cc = args.cc

    def run(self):
        """Execute the command"""

        language_code = self.get_language_code()
        if language_code is None:
            language_code = "unk"

        act = {
            "to": [],
            "cc": [],
            "type": "Create",
            "object": {
                "type": "Collection",
                "nameMap": {
                    language_code: self.name,
                }
            },
        }

        if self.public:
            act["to"].append("https://www.w3.org/ns/activitystreams#Public")
        elif self.followers_only:
            actor = self.logged_in_actor()
            if actor is None:
                raise Exception("Not logged in")
            followers = actor.get("followers", None)
            if followers is None:
                raise Exception("No followers collection found")
            followers_id = self.to_id(followers)
            act["to"].append(followers_id)
        elif self.private:
            pass

        if self.to:
            for to in self.to:
                act["to"].append(self.get_actor_id(to))
        if self.cc:
            for cc in self.cc:
                act["cc"].append(self.get_actor_id(cc))

        result = self.do_activity(act)

        print(json.dumps(result, indent=4))