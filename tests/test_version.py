import unittest
from unittest.mock import patch, mock_open, MagicMock
from ap.main import run_command
from argparse import Namespace
import io
import sys
import json

ACTOR_ID = "evanp@social.example"

SEMVER_REGEX = r'^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'

TOKEN_FILE_DATA = json.dumps({"actor_id": ACTOR_ID, "access_token": "12345678"})

class TestVersionCommand(unittest.TestCase):
    def setUp(self):
        self.held, sys.stdout = sys.stdout, io.StringIO()  # Redirect stdout

    def tearDown(self):
        sys.stdout = self.held

    @patch("builtins.open", new_callable=mock_open, read_data=TOKEN_FILE_DATA)
    def test_version(self, mock_file):
        run_command(["version"], {})

        # Assertions
        output = sys.stdout.getvalue()
        self.assertRegex(output, r'^ap ')
        self.assertRegex(output[3:], SEMVER_REGEX)

if __name__ == "__main__":
    unittest.main()
