from .command import Command
import json
import html

class CreateNoteCommand(Command):
    def __init__(self, args, env):
        super().__init__(args, env)
        self.source = " ".join(args.source)
        self.public = args.public
        self.followers_only = args.followers_only
        self.private = args.private
        self.to = args.to
        self.cc = args.cc
        self.in_reply_to = args.in_reply_to

    def run(self):
        obj = {
            "type": "Note",
            "source": {
                "mediaType": "text/plain",
                "content": self.source
            },
            "tags": self.getTags(self.source),
            "content": self.sourceToHTML(self.source)
        }
        if self.in_reply_to:
            obj["inReplyTo"] = self.in_reply_to

        act = {
            "to": [],
            "cc": [],
            "type": "Create",
             "object": obj
        }

        if self.public:
            act["to"].append("https://www.w3.org/ns/activitystreams#Public")
        elif self.followers_only:
            actor = self.logged_in_actor()
            if actor is None:
                raise Exception("Not logged in")
            followers = actor.get("followers", None)
            if followers is None:
                raise Exception("No followers collection found")
            followers_id = self.to_id(followers)
            act["to"].append(followers_id)
        elif self.private:
            pass

        if self.to:
            for to in self.to:
                act["to"].append(self.get_actor_id(to))
        if self.cc:
            for cc in self.cc:
                act["cc"].append(self.get_actor_id(cc))

        result = self.do_activity(act)

        print(json.dumps(result, indent=4))

    def getTags(self, source):
        return None

    def sourceToHTML(self, source):
        return html.escape(source) 