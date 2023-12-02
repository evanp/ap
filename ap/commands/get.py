from .command import Command
import json


class GetCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.id = args.id

    def run(self):
        data = self.get_object(self.id)
        print(json.dumps(data, indent=4))
