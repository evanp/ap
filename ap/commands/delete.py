from .command import Command


class DeleteCommand(Command):
    def __init__(self, args):
        super().__init__(args)
        self.id = args.id
        self.force = args.force

    def run(self):
        """Delete an object

        Args:
            id (str): The ID of the object to delete
        """

        obj = self.get_object(self.id)

        if obj is None:
            raise Exception(f"Object {self.id} not found")

        name = self.to_text(obj)

        if name is None:
            name = f'a {obj["type"]} object'

        if not self.force:
            prompt = f"Are you sure you want to delete {name} ({self.id}) [y/N]?"
            confirmation = input(prompt).lower()
            if confirmation != "y":
                return

        result = self.do_activity(
            {
                "@context": "https://www.w3.org/ns/activitystreams",
                "type": "Delete",
                "object": self.id,
            }
        )

        print("Deleted.")
