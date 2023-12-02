from .command import Command


class LogoutCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)

    def run(self):
        token_file = self.token_file()

        if not token_file.exists():
            print("Not logged in")
            return

        token_file.unlink()
        print("Logged out")
