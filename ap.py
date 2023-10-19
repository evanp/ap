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

    get_parser = subparsers.add_parser('get', help='Get an object by ID')
    get_parser.add_argument('id', help='id of object to get')

    inbox_parser = subparsers.add_parser('inbox', help='Get inbox')
    inbox_parser.add_argument('--offset', help='Offset to start at', default=0, type=int)
    inbox_parser.add_argument('--limit', help='Max items to get', default=10, type=int)

    outbox_parser = subparsers.add_parser('outbox', help='Get outbox')
    outbox_parser.add_argument('--offset', help='Offset to start at', default=0, type=int)
    outbox_parser.add_argument('--limit', help='Max items to get', default=10, type=int)

    create_parser = subparsers.add_parser('create', help='Create objects')
    subsubparsers = create_parser.add_subparsers(dest='subsubcommand')
    note_parser = subsubparsers.add_parser('note', help='Create a note')
    note_parser.add_argument('content', nargs='+', help='Content of the note')
    group = note_parser.add_mutually_exclusive_group()
    group.add_argument('--private', action='store_true', default=True, help='Whether the note is private')
    group.add_argument('--public', action='store_true', help='Whether the note is public')
    group.add_argument('--followers-only', action='store_true', help='Whether the note is followers-only')
    note_parser.add_argument('--to', type=str, nargs='+', help='Additional recipients')
    note_parser.add_argument('--cc', type=str, nargs='+', help='Additional CC recipients')
    args = parser.parse_args()

    if args.subcommand == 'login':
        command = commands.LoginCommand(args)
    elif args.subcommand == 'get':
        command = commands.GetCommand(args)
    elif args.subcommand == 'inbox':
        command = commands.InboxCommand(args)
    elif args.subcommand == 'outbox':
        command = commands.OutboxCommand(args)
    elif args.subcommand == 'create':
        if args.subsubcommand == 'note':
            command = commands.CreateNoteCommand(args)
        else:
            raise Exception(f"Unknown subsubcommand: {args.subsubcommand}")
    else:
        raise Exception(f"Unknown command: {args.subcommand}")

    command.run()

if __name__ == '__main__':
    main()
