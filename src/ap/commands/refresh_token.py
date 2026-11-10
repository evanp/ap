from .command import Command


class RefreshTokenCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)

    def run(self):
        id = self.logged_in_actor_id()
        if id is None:
            raise Exception("Not logged in")   
        token = self.refresh_token(id)
        print(f"refreshed token for  {id}")
