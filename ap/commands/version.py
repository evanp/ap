from .command import Command
from ..version import __version__

class VersionCommand(Command):

    def __init__(self, args, env):
        super().__init__(args, env)

    def run(self):
        print(f"ap {__version__}")
