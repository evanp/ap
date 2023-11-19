from .command import Command


class AcceptFollowerCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.id = args.id

    def run(self):
        actor_id = self.get_actor_id(self.id)

        if actor_id is None:
            print("No actor found for %s" % self.id)
            return

        coll = self.get_actor_collection("pendingFollowers")

        found = None

        for item in self.items(coll):
            activity = self.to_object(item, ["actor", "type"])
            if "actor" not in activity:
                continue
            if actor_id == self.to_id(activity["actor"]):
                found = activity
                break

        if found is None:
            print("No pending follower found for %s" % self.id)
            return

        act = {
            "type": "Accept",
            "object": {"type": found["type"], "actor": actor_id, "id": found["id"]},
            "to": [actor_id],
        }

        self.do_activity(act)

        print("Accepted follower %s" % self.id)
