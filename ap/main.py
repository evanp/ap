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
    note_parser.add_argument("--to", type=str, action='append', help="Additional recipients")
    note_parser.add_argument(
        "--cc", type=str, action='append', help="Additional CC recipients"
    )
    note_parser.add_argument('--in-reply-to', type=str, help="Object to reply to")

    coll_parser = subsubparsers.add_parser("collection", help="Create a collection")
    coll_parser.add_argument("name", nargs="+", help="Name of the collection")
    coll_group = coll_parser.add_mutually_exclusive_group()
    coll_group.add_argument(
        "--private",
        action="store_true",
        default=True,
        help="Whether the collection is private",
    )
    coll_group.add_argument(
        "--public", action="store_true", help="Whether the collection is public"
    )
    coll_group.add_argument(
        "--followers-only",
        action="store_true",
        help="Whether the collection is followers-only",
    )
    coll_parser.add_argument("--to", type=str, action='append', help="Additional recipients")
    coll_parser.add_argument(
        "--cc", type=str, action='append', help="Additional CC recipients"
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

    undo_like_parser = undo_subparsers.add_parser("like", help="Undo a like")
    undo_like_parser.add_argument("id", help="id of object to unlike")

    undo_share_parser = undo_subparsers.add_parser("share", help="Undo a share")
    undo_share_parser.add_argument("id", help="id of object to unshare")

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

    add_parser = subparsers.add_parser("add", help="Add objects to collections")
    add_parser.add_argument("--target", help="ID of the collection to add to")
    add_parser.add_argument("id", action='append', help="ID of the object(s) to add")

    remove_parser = subparsers.add_parser("remove", help="Remove objects from collections")
    remove_parser.add_argument("--target", help="ID of the collection to remove from")
    remove_parser.add_argument("id", action='append', help="ID(s) of the object(s) to remove")

    likes_parser = subparsers.add_parser("likes", help="Get likes of an object")
    likes_parser.add_argument("id", help="ID of the object to get likes of")
    likes_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    likes_parser.add_argument("--limit", help="Max items to get", default=10, type=int)

    like_parser = subparsers.add_parser("like", help="Like an object")
    like_parser.add_argument("id", help="ID of the object to like")

    subparsers.add_parser("version", help="Show version information")

    shares_parser = subparsers.add_parser("shares", help="Get shares of an object")
    shares_parser.add_argument("id", help="ID of the object to get shares of")
    shares_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    shares_parser.add_argument("--limit", help="Max items to get", default=10, type=int)

    share_parser = subparsers.add_parser("share", help="Share an object")
    share_parser.add_argument("id", help="ID of the object to share")

    replies_parser = subparsers.add_parser("replies", help="Get replies of an object")
    replies_parser.add_argument("id", help="ID of the object to get replies of")
    replies_parser.add_argument(
        "--offset", help="Offset to start at", default=0, type=int
    )
    replies_parser.add_argument("--limit", help="Max items to get", default=10, type=int)

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
        "create": {
            "note": commands.CreateNoteCommand,
            "collection": commands.CreateCollectionCommand,
        },
        "pending": {
            "followers": commands.PendingFollowersCommand,
            "following": commands.PendingFollowingCommand,
        },
        "accept": {"follower": commands.AcceptFollowerCommand},
        "reject": {"follower": commands.RejectFollowerCommand},
        "undo": {
            "follow": commands.UndoFollowCommand,
            "like": commands.UndoLikeCommand,
            "share": commands.UndoShareCommand,
        },
        "upload": commands.UploadCommand,
        "delete": commands.DeleteCommand,
        "update": {"note": commands.UpdateNoteCommand},
        "add": commands.AddCommand,
        "remove": commands.RemoveCommand,
        "likes": commands.LikesCommand,
        "version": commands.VersionCommand,
        "like": commands.LikeCommand,
        "shares": commands.SharesCommand,
        "share": commands.ShareCommand,
        "replies": commands.RepliesCommand
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

    command = entry(args, env)

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
