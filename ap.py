#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This is the main entrypoint for the ap ActivityPub command
line client.

Functions:
    main(): Parses arguments and calls corresponding commands
"""

import argparse
import commands

def main():
    parser = argparse.ArgumentParser(description='ActivityPub command line client')
    subparsers = parser.add_subparsers(dest='subcommand')

    login_parser = subparsers.add_parser('login', help='Log into an ActivityPub server')
    login_parser.add_argument('id', nargs=argparse.REMAINDER, help='Webfinger or ActivityPub ID')
    create_parser = subparsers.add_parser('create', help='Create new content')
    create_parser.add_argument('--public', help='Make content public', action='store_true')
    typeparsers = create_parser.add_subparsers(dest='type')
    note_parser = typeparsers.add_parser('note', help='Create a new note')
    note_parser.add_argument('text', nargs=argparse.REMAINDER, help='Note text')

    inbox_parser = subparsers.add_parser('inbox', help='View inbox')
    outbox_parser = subparsers.add_parser('outbox', help='View outbox')
    followers_parser = subparsers.add_parser('followers', help='View followers')
    following_parser = subparsers.add_parser('following', help='View following')
    liked_parser = subparsers.add_parser('liked', help='View liked items')

    args = parser.parse_args()

    if args.subcommand == 'login':
        commands.login(args.id)
    elif args.subcommand == 'create':
        if args.type == 'note':
            commands.create_note(args.text, args.public, args.followers_only)
        else:
            print(f"Unknown type: {args.type}")
    elif args.subcommand == 'inbox':
        commands.inbox()
    elif args.subcommand == 'outbox':
        commands.outbox()
    elif args.subcommand == 'followers':
        commands.followers()
    elif args.subcommand == 'following':
        commands.following()
    elif args.subcommand == 'liked':
        commands.liked()
    else:
        print(f"Unknown command: {args.subcommand}")

if __name__ == '__main__':
    main()
