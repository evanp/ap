from .command import Command

class UndoShareCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

    def run(self):

        actor = self.logged_in_actor()

        actor_id = self.to_id(actor)

        obj = self.get_object(self.id)

        if (obj is None):
            raise Exception(f"Could not find {self.id} object")

        if ("shares" not in obj):
            raise Exception(f"{self.id} object does not have shares collection")

        shares = self.to_id(obj["shares"])

        activity = None

        for item in self.items(shares):
            share = self.to_object(item, ["actor"])
            if self.to_id(share["actor"]) == actor_id:
                activity = share
                break

        if (activity is None):
            raise Exception(f"Could not find share for {self.id} object")

        result = self.do_activity({
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Undo",
            "object": activity
        })

        print(f'Undid share activity {activity["id"]} of object {self.id} with result {result["id"]}')