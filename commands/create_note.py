from .command import Command
import json

class CreateNoteCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.content = ' '.join(args.content)
        self.public = args.public
        self.followers_only = args.followers_only
        self.private = args.private
        self.to = args.to
        self.cc = args.cc

    def run(self):
        act = {
            'to': [],
            'cc': [],
            'type': 'Create',
            'object': {
                'type': 'Note',
                'content': self.content,
            }
        }

        if self.public:
            act['to'].append('https://www.w3.org/ns/activitystreams#Public')
        elif self.followers_only:
            actor = self.logged_in_actor()
            if actor is None:
                raise Exception("Not logged in")
            followers = actor.get('followers', None)
            if followers is None:
                raise Exception("No followers collection found")
            followers_id = self.to_id(followers)
            act['to'].append(followers_id)
        elif self.private:
            pass

        if self.to:
            for to in self.to:
                act['to'].append(self.actor_id(to))
        if self.cc:
            for cc in self.cc:
                act['cc'].append(self.actor_id(cc))

        result = self.do_activity(act)

        print(json.dumps(result, indent=4))