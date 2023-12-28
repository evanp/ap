from .command import Command
import json

class UpdateNoteCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.id = args.id
        self.content = args.content

    def run(self):
        result = self.do_activity({
            "type": "Update",
            "object": {
                "type": "Note",
                "id": self.id,
                "content": self.content,
            }
        })
        print(json.dumps(result, indent=4))