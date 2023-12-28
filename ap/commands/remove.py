from .command import Command

class RemoveCommand(Command):
    """Remove an object from a collection."""

    def __init__(self, args, env):
        super().__init__(args, env)
        self.target = args.target
        self.id = args.id

    def run(self):
        """Run the command."""

        if type(self.id) == list and len(self.id) == 1:
            obj = self.id[0]
        else:
            obj = self.id[0]

        result = self.do_activity({
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Remove",
            "target": self.target,
            "object": obj
        })

        print(result["id"])