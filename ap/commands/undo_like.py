from .command import Command

class UndoLikeCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

    def run(self):

        actor = self.logged_in_actor()

        actor_id = self.to_id(actor)

        if "liked" not in actor:
            raise Exception(f"Actor {actor_id} does not have liked collection")

        found = False

        for item in self.items(actor["liked"]):
            item_id = self.to_id(item)
            if item_id == self.id:
                found = True
                break

        if not found:
            raise Exception(f"Actor {actor_id} has not liked object {self.id}")
            
        obj = self.get_object(self.id)

        if (obj is None):
            raise Exception(f"Could not find {self.id} object")

        if ("likes" not in obj):
            raise Exception(f"{self.id} object does not have likes collection")

        likes = self.to_id(obj["likes"])

        activity = None

        for item in self.items(likes):
            like = self.to_object(item, ["actor"])
            if self.to_id(like["actor"]) == actor_id:
                activity = like
                break

        if (activity is None):
            raise Exception(f"Could not find like for {self.id} object")

        result = self.do_activity({
            "@context": "https://www.w3.org/ns/activitystreams",
            "type": "Undo",
            "object": activity
        })

        print(f'Undid like activity {activity["id"]} of object {self.id} with result {result["id"]}')