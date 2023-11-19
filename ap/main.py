#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This is the main entrypoint for the ap ActivityPub command
line client.

Functions:
    main(): Parses arguments and calls corresponding commands
"""

import sys
import os
import argparse
import ap.commands as commands

# Create the top-level parser

def make_parser():
    """Create the top-level parser"""

    parser = argparse.ArgumentParser(description="ActivityPub command line client")
    subparsers = parser.add_subparsers(dest="subcommand")

    login_parser = subparsers.add_parser("login", help="Log into an ActivityPub server")
    login_parser.add_argument("id", help="Webfinger or ActivityPub ID")

    subparsers.add_parser("logout", help="Log out of the current session")

    subparsers.add_parser("whoami", help="Show the current user")

    get_parser = subparsers.add_parser("get", help="Get an object by ID")
    get_parser.add_argument("id", help="id of object to get")

    inbox_parser = subparsers.add_parser("inbox", help="Get inbox")
    inbox_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    inbox_parser.add_argument("--limit", help="Max items to get", default=10, type=int)

    outbox_parser = subparsers.add_parser("outbox", help="Get outbox")
    outbox_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    outbox_parser.add_argument("--limit", help="Max items to get", default=10, type=int)

    followers_parser = subparsers.add_parser("followers", help="Get followers")
    followers_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    followers_parser.add_argument(
        "--limit", help="Max items to get", default=10, type=int
    )

    following_parser = subparsers.add_parser("following", help="Get following")
    following_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    following_parser.add_argument(
        "--limit", help="Max items to get", default=10, type=int
    )

    follow_parser = subparsers.add_parser("follow", help="Follow an actor")
    follow_parser.add_argument("id", help="id of actor to follow")

    pending_parser = subparsers.add_parser(
        "pending", help="Get pending follow requests"
    )
    pending_subparsers = pending_parser.add_subparsers(dest="subsubcommand")

    pending_followers_parser = pending_subparsers.add_parser(
        "followers", help="Show pending incoming follow requests"
    )
    pending_followers_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    pending_followers_parser.add_argument(
        "--limit", help="Max items to get", default=10, type=int
    )

    pending_following_parser = pending_subparsers.add_parser(
        "following", help="Show pending outgoing follow requests"
    )
    pending_following_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    pending_following_parser.add_argument(
        "--limit", help="Max items to get", default=10, type=int
    )

    create_parser = subparsers.add_parser("create", help="Create objects")
    subsubparsers = create_parser.add_subparsers(dest="subsubcommand")
    note_parser = subsubparsers.add_parser("note", help="Create a note")
    note_parser.add_argument("content", nargs="+", help="Content of the note")
    group = note_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--private",
        action="store_true",
        default=True,
        help="Whether the note is private",
    )
    group.add_argument(
        "--public", action="store_true", help="Whether the note is public"
    )
    group.add_argument(
        "--followers-only",
        action="store_true",
        help="Whether the note is followers-only",
    )
    note_parser.add_argument("--to", type=str, nargs="+", help="Additional recipients")
    note_parser.add_argument(
        "--cc", type=str, nargs="+", help="Additional CC recipients"
    )

    accept_parser = subparsers.add_parser("accept", help="Accept an activity")
    accept_subparsers = accept_parser.add_subparsers(dest="subsubcommand")
    accept_follower_parser = accept_subparsers.add_parser(
        "follower", help="Accept a follower request"
    )
    accept_follower_parser.add_argument("id", help="id of follower to accept")

    reject_parser = subparsers.add_parser("reject", help="Reject an activity")
    reject_subparsers = reject_parser.add_subparsers(dest="subsubcommand")
    reject_follower_parser = reject_subparsers.add_parser(
        "follower", help="Reject a follower request"
    )
    reject_follower_parser.add_argument("id", help="id of follower to reject")

    undo_parser = subparsers.add_parser("undo", help="Undo an activity")
    undo_subparsers = undo_parser.add_subparsers(dest="subsubcommand")
    undo_follow_parser = undo_subparsers.add_parser("follow", help="Undo a follow")
    undo_follow_parser.add_argument("id", help="id of actor to stop following")

    upload_parser = subparsers.add_parser("upload", help="Upload a file")
    upload_parser.add_argument("filename", help="file name to upload")
    group = upload_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--private",
        action="store_true",
        default=True,
        help="Whether the file is private",
    )
    group.add_argument(
        "--public", action="store_true", help="Whether the file is public"
    )
    group.add_argument(
        "--followers-only",
        action="store_true",
        help="Whether the file is followers-only",
    )
    upload_parser.add_argument(
        "--to", type=str, nargs="+", help="Additional recipients"
    )
    upload_parser.add_argument(
        "--cc", type=str, nargs="+", help="Additional CC recipients"
    )
    upload_parser.add_argument("--title", help="Title of the file")
    upload_parser.add_argument("--description", help="Description of the file")

    delete_parser = subparsers.add_parser("delete", help="Delete an object")
    delete_parser.add_argument("id", help="id of object to delete")
    delete_parser.add_argument(
        "--force", action="store_true", help="Do not prompt for confirmation"
    )

    update_parser = subparsers.add_parser("update", help="Update objects")
    update_subsubparsers = update_parser.add_subparsers(dest="subsubcommand")
    update_note_parser = update_subsubparsers.add_parser("note", help="Update a note")
    update_note_parser.add_argument("id", help="ID of the note to update")
    update_note_parser.add_argument("content", nargs="+", help="Content of the note")

    return parser

parser = make_parser()

def get_command(args, env):
    """Get the command corresponding to the arguments"""

    command = None
    entry = None

    map = {
        "login": commands.LoginCommand,
        "logout": commands.LogoutCommand,
        "whoami": commands.WhoamiCommand,
        "get": commands.GetCommand,
        "inbox": commands.InboxCommand,
        "outbox": commands.OutboxCommand,
        "followers": commands.FollowersCommand,
        "following": commands.FollowingCommand,
        "follow": commands.FollowCommand,
        "create": {"note": commands.CreateNoteCommand},
        "pending": {
            "followers": commands.PendingFollowersCommand,
            "following": commands.PendingFollowingCommand,
        },
        "accept": {"follower": commands.AcceptFollowerCommand},
        "reject": {"follower": commands.RejectFollowerCommand},
        "undo": {"follow": commands.UndoFollowCommand},
        "upload": commands.UploadCommand,
        "delete": commands.DeleteCommand,
        "update": {"note": commands.UpdateNoteCommand},
    }

    if args.subcommand in map:
        entry = map[args.subcommand]
        if isinstance(entry, dict):
            if args.subsubcommand in entry:
                entry = entry[args.subsubcommand]
            else:
                raise Exception("Invalid subsubcommand")
    else:
        raise Exception("Invalid subcommand")

    command = entry(args)

    return command

def run_command(argv, env=None):

    """Run a command"""

    if env is None:
        env = os.environ

    args = parser.parse_args(argv)

    command = get_command(args, env)

    command.run()

def main():
    """Parse arguments and call corresponding commands"""

    run_command(sys.argv[1:], os.environ)


if __name__ == "__main__":
    main()