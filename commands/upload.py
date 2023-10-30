from .command import Command
from pathlib import Path
import mimetypes
import json

class UploadCommand(Command):

    def __init__(self, args):
        super().__init__(args)
        self.filename = args.filename
        self.title = args.title
        self.description = args.description
        self.public = args.public
        self.followers_only = args.followers_only
        self.private = args.private
        self.to = args.to
        self.cc = args.cc

    def run(self):
        actor = self.logged_in_actor()
        if actor is None:
            raise Exception('Not logged in')
        if 'endpoints' not in actor:
            raise Exception('No endpoints found')
        if 'uploadMedia' not in actor['endpoints']:
            raise Exception('No uploadMedia endpoint found')
        uploadMedia = actor['endpoints']['uploadMedia']
        path = Path(self.filename)
        if not path.exists():
            raise Exception('File not found: %s' % self.filename)
        if not path.is_file():
            raise Exception('Not a file: %s' % self.filename)
        type, encoding = mimetypes.guess_type(path)
        if type is None:
            raise Exception('Could not determine file type')
        major = type.split('/')[0]

        obj = {
            "type": self.ap_type(major)
        }

        lc = self.get_language_code()

        if self.title:
            obj['nameMap'] = {}
            obj['nameMap'][lc] = self.title

        if self.description:
            obj['summaryMap'] = {}
            obj['summaryMap'][lc] = self.description

        if self.public:
            obj['to'] = ['https://www.w3.org/ns/activitystreams#Public']
        elif self.followers_only:
            if 'followers' not in actor:
                raise Exception('No followers collection found')
            followers = actor['followers']
            followers_id = self.to_id(followers)
            obj['to'] = [followers_id]

        if self.to:
            for to in self.to:
                obj['to'].append(self.get_actor_id(to))
        if self.cc:
            for cc in self.cc:
                obj['cc'].append(self.get_actor_id(cc))

        file_data = (path.name, path.open('rb'), type)

        object_data = json.dumps(obj)

        multipart_form_data = {
            'file': file_data,
            'object': ('descriptor.jsonld', object_data, 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"')
        }

        oauth = self.session()
        res = oauth.post(uploadMedia, files=multipart_form_data)
        if res.status_code != 201:
            raise Exception('Upload failed: %s' % res.text)
        result = res.json()
        print(result)

    def ap_type(self, major):
        if major == 'image':
            return 'Image'
        elif major == 'video':
            return 'Video'
        elif major == 'audio':
            return 'Audio'
        elif major == 'text':
            return 'Article'
        else:
            return 'Document'