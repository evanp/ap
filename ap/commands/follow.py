from .command import Command
import json


class FollowCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.id = args.id

    def run(self):
        actor_id = self.get_actor_id(self.id)
        if actor_id is None:
            raise Exception("Actor not found")

        act = {"type": "Follow", "object": actor_id, "to": [actor_id]}

        result = self.do_activity(act)

        print(json.dumps(result, indent=4))
