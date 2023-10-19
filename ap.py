#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This is the main entrypoint for the ap ActivityPub command
line client.

Functions:
    main(): Parses arguments and calls corresponding commands
"""

import argparse
import commands
import requests
from requests.sessions import Session

# Create a session
s = Session()
s.verify = False
requests.Session = lambda *args, **kwargs: s

def main():
    parser = argparse.ArgumentParser(description='ActivityPub command line client')
    subparsers = parser.add_subparsers(dest='subcommand')

    login_parser = subparsers.add_parser('login', help='Log into an ActivityPub server')
    login_parser.add_argument('id', help='Webfinger or ActivityPub ID')

    args = parser.parse_args()

    if args.subcommand == 'login':
        command = commands.LoginCommand(args)
    else:
        print(f"Unknown command: {args.subcommand}")

    command.run()

if __name__ == '__main__':
    main()
