from .command import Command

class WhoamiCommand(Command):

    def __init__(self, args):
        super().__init__(args)

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            print('Not logged in')
            return

        print(self.to_webfinger(actor))