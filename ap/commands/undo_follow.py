from .command import Command


class UndoFollowCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.id = args.id

    def run(self):
        actor_id = self.get_actor_id(self.id)

        if actor_id is None:
            print("No actor found for %s" % self.id)
            return

        # Try pending first (we might get lucky)

        coll = self.get_actor_collection("pendingFollowing")

        found = None

        for item in self.items(coll):
            activity = self.to_object(item, ["object", "type"])
            if actor_id == self.to_id(activity["object"]):
                found = activity
                break

        if found is None:
            coll = self.get_actor_collection("outbox")

            found = None

            for item in self.items(coll):
                activity = self.to_object(item, ["object", "type"])
                if "type" not in activity:
                    continue
                if "object" not in activity:
                    continue
                type = activity["type"]
                if isinstance(type, list):
                    if "Follow" not in type:
                        continue
                elif type != "Follow":
                    continue
                if actor_id == self.to_id(activity["object"]):
                    found = activity
                    break

        if found is None:
            print("No follow found for %s" % self.id)
            return

        act = {
            "type": "Undo",
            "object": {"type": found["type"], "object": actor_id, "id": found["id"]},
            "to": [actor_id],
        }

        self.do_activity(act)

        print("Unfollowed %s" % self.id)
