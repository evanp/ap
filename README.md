# ap

[![license](https://img.shields.io/github/license/evanp/ap.svg)](LICENSE)
[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

`ap` is a command-line client for the [ActivityPub](https://www.w3.org/TR/activitypub/) API.

## Table of Contents

- [Background](#background)
- [Install](#install)
- [Usage](#usage)
- [Maintainers](#maintainers)
- [Contributing](#contributing)
- [License](#license)

## Background

I initially developed this program to illustrate how to write client code for the ActivityPub API as part of my book for O'Reilly Media, "ActivityPub: Programming for the Social Web".

Note that not all servers that implement the ActivityPub *federation protocol* necessarily implement the ActivityPub *API*. In particular, as of this writing, [Mastodon](https://joinmastodon.org/) does not implement the ActivityPub API; it has its own API. If you're using Mastodon, you may prefer the [toot](https://github.com/ihabunek/toot) CLI instead.

A good list of supporting software is here:

  https://codeberg.org/fediverse/delightful-fediverse-experience/issues/130

## Install

The easiest way to install is from [PyPI](https://pypi.org/).

```bash
pipx install activitypub-cli
```

## Usage

`ap` uses the subcommand pattern common with other large command-line programs like `git` and `docker`.  The full list of subcommands is available by typing `ap --help`. Familiarity with the ActivityPub API is helpful for understanding these commands!

### `ap login <id>`

Logs in as a user to an ActivityPub API server using OAuth 2.0. The `<id>` argument is a [Webfinger](https://www.w3.org/community/reports/socialcg/CG-FINAL-apwf-20240608/) ID like `username@domain.example` or the ActivityPub [Actor ID](https://www.w3.org/TR/activitypub/#actors) (usually an HTTPS URL).

Example with a Webfinger ID:

```bash
ap login username@domain.example
```

Example with an ActivityPub actor ID:

```bash
ap login https://social.example/person/df816567-4c64-480c-955a-0f734bf93362
```

`ap login` stores the OAuth 2.0 token(s) in a file in the user's home directory, `$HOME/.ap/token.json`, so that subsequent commands can use them.

If this command fails, it's likely that your server doesn't support the ActivityPub API.

### `ap logout`

Logs out of the current session by deleting the token file.

### `ap refresh_token`

Refresh the access token (It will do this automatically for most operations if needed when access token has expired).

### `ap whoami`

Shows the currently logged-in user.

### `ap get <id>`

Gets the object with the given ID and prints it to stdout.

### `ap inbox`

### `ap outbox`

### `ap followers`

### `ap following`

### `ap pending followers`

### `ap pending following`

Shows these collections for the currently logged-in user.

### `ap follow <id>`

Follows the user with the given ID.

### `ap accept follower <id>`

### `ap reject follower <id>`

Accepts or rejects a follow request from the user with the given ID.

### `ap undo follow <id>`

Unfollows the user with the given ID.

### `ap create note <text>`

Creates a Note object with the given text.

### `ap upload <filename>`

Uploads the given file and prints the resulting URL.

## Maintainers

- [@evanp](https://github.com/evanp) (Evan Prodromou; [@evan@cosocial.ca](https://cosocial.ca/users/evan) on Mastodon)

## Contributing

The project uses [uv](https://docs.astral.sh/uv/). To get set up, clone from Git and set up a virtual environment:

```bash
git clone https://github.com/evanp/ap.git
cd ap
uv venv
source .venv/bin/activate
uv pip install -e .
```

Then you can run the application directly:

```bash
ap -h
```

I'm very interested in contributions to this project. Some quick notes:

- Please open an issue before starting work on a new feature. This will help us coordinate and make sure that the feature is a good fit for the project.
- Ideally, commands should map closely to the ActivityPub API. If you're not sure how to do that, please open an issue and we can discuss it.
- Please make sure that your code passes the existing tests, and add new tests as appropriate.
- Please make your code format correctly with [Python Black](https://black.readthedocs.io/).

Small note: If editing the Readme, please conform to the [standard-readme](https://github.com/RichardLitt/standard-readme) specification.

## License

[GPL v3 or later](../LICENSE)
