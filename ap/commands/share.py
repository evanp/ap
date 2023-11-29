from .command import Command

class ShareCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

    def run(self):

        result = self.do_activity({
            "type": "Announce",
            "object": self.id
        })

        print(f'Share activity: {result["id"]}')