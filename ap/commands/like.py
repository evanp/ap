from .command import Command

class LikeCommand(Command):
    """Like an object"""

    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

    def run(self):
        result = self.do_activity({
            "type": "Like",
            "object": self.id,
        })
        print(result["id"])
