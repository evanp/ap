import requests
import webfinger
from pathlib import Path
import json
from requests_oauthlib import OAuth2Session
from urllib.parse import urlparse
import itertools
import re
from typing import Generator, Dict
from ap.version import __version__
from html import escape
import logging

AS2 = "https://www.w3.org/ns/activitystreams#"

USER_AGENT = f"ap/{__version__}"
BASE_HEADERS = {
    "Accept": "application/ld+json,application/activity+json,application/json",
    "User-Agent": USER_AGENT
}
TAG_NAMESPACE = "https://tags.pub/"

class Command:
    def __init__(self, args, env):
        self.args = args
        self.env = env
        self._logged_in_actor = None
        self._logged_in_actor_id = None
        self._token_file_data = None
        self._session = None
        self._language_code = None
        self._tag_namespace = TAG_NAMESPACE

    def logged_in_actor_id(self) -> str:
        if self._logged_in_actor_id is None:
            token = self.token_file_data()
            self._logged_in_actor_id = token.get("actor_id", None)
            if self._logged_in_actor_id is None:
                raise Exception("Not logged in")
        return self._logged_in_actor_id

    def token_file(self) -> Path:
        home = self.env.get('HOME')
        return Path(home) / ".ap" / "token.json"

    def token_file_data(self) -> dict:
        if self._token_file_data is None:
            token_file = self.token_file()
            with open(token_file, "r") as f:
                self._token_file_data = json.loads(f.read())
        return self._token_file_data

    def logged_in_actor(self) -> dict:
        if self._logged_in_actor is None:
            id = self.logged_in_actor_id()
            oauth = self.session()
            r = oauth.get(id, headers=BASE_HEADERS)
            r.raise_for_status()
            self._logged_in_actor = r.json()
        return self._logged_in_actor

    def session(self) -> OAuth2Session:
        if self._session is None:
            token = self.token_file_data()
            self._session = OAuth2Session(token=token)
        return self._session

    def to_id(self, prop: dict|str) -> str:
        if isinstance(prop, str):
            return prop
        elif isinstance(prop, dict):
            if "id" in prop:
                return prop["id"]
            else:
                raise Exception("No id found")
        else:
            raise Exception(f'Invalid property type for {prop}')

    def to_object(self, obj: dict|str, required: list=[]) -> dict:
        if isinstance(obj, str):
            return self.get_object(obj)
        else:
            if all(r in obj for r in required if isinstance(r, str)) and all(
                any(opt in obj for opt in r) for r in required if isinstance(r, list)
            ):
                return obj
            elif obj.get("id", None) is not None:
                return self.get_object(obj.get("id"))
            else:
                raise Exception("Cannot satisfy requirements")

    def to_webfinger(self, obj: dict|str) -> str:
        obj = self.to_object(obj, ["id", ["preferredUsername", "webfinger"]])
        if "webfinger" in obj:
            return obj["webfinger"]
        if "id" not in obj or "preferredUsername" not in obj:
            raise Exception("Cannot format this as a webfinger")
        return obj["preferredUsername"] + "@" + urlparse(obj["id"]).netloc

    def is_webfinger_id(self, id: str) -> bool:
        if self.is_activitypub_id(id):
            return False
        return re.match(r"^(acct:)?@?[^@]+@[^@]+$", id) is not None

    def is_activitypub_id(self, id: str) -> bool:
        return re.match(r"https:\/\/[\w.-]+(?:\.[\w.-]+)+[\w\-\._~:/?#[\]@!$&'()*+,;=]*", id) is not None

    def to_webfinger_url(self, id: str) -> str:
        if id.startswith("@"):
            id = "acct:" + id[1:]
        elif id.startswith("acct:"):
            pass
        else:
            id = "acct:" + id
        return id

    def to_activitypub_id(self, id: str) -> str:
        url = self.to_webfinger_url(id)
        wf = webfinger.finger(url)
        matches = [
            l["href"]
            for l in wf.links
            if l["rel"] == "self" and l["type"] == "application/activity+json"
        ]
        if len(matches) == 0:
            raise Exception("No ActivityPub account found")
        return matches[0]

    def get_actor_id(self, id: str) -> str:
        if self.is_activitypub_id(id):
            return id
        elif self.is_webfinger_id(id):
            return self.to_activitypub_id(id)
        else:
            raise Exception("Invalid id")

    def get_public(self, id: str) -> dict:
        r = requests.get(id, headers=BASE_HEADERS)
        r.raise_for_status()
        return r.json()

    def get_object(self, id: str) -> dict:
        actor_id = self.logged_in_actor_id()
        if actor_id is None:
            raise Exception("Not logged in")
        if urlparse(id).netloc == urlparse(actor_id).netloc:
            data = self.get_local(id)
        else:
            data = self.get_by_proxy(id)
        return data

    def get_local(self, id: str) -> dict:
        oauth = self.session()
        r = oauth.get(id, headers=BASE_HEADERS)
        r.raise_for_status()
        return r.json()

    def get_by_proxy(self, id: str) -> dict:
        actor = self.logged_in_actor()
        proxyUrl = self.get_endpoint(actor, "proxyUrl")
        oauth = self.session()
        r = oauth.post(proxyUrl, headers=BASE_HEADERS, data={"id": id})
        r.raise_for_status()
        return r.json()

    def items(self, obj: dict|str) -> Generator[dict, None, None]:
        coll = self.to_object(obj, [["items", "orderedItems", "first"]])
        if "items" in coll:
            for item in coll["items"]:
                yield item
            return
        elif "orderedItems" in coll:
            for item in coll["orderedItems"]:
                yield item
            return
        elif "first" in coll:
            page = self.to_object(coll["first"], [["items", "orderedItems"]])
            while page is not None:
                if "items" in page:
                    for item in page["items"]:
                        yield item
                elif "orderedItems" in page:
                    for item in page["orderedItems"]:
                        yield item
                else:
                    raise Exception("No items found in page")
                if "next" in page:
                    page = self.to_object(page["next"], [["items", "orderedItems"]])
                else:
                    page = None

    def do_activity(self, act: dict) -> dict:
        actor = self.logged_in_actor()
        if "outbox" not in actor:
            raise Exception("No outbox found")
        outbox_id = self.to_id(actor["outbox"])
        oauth = self.session()
        headers = {**BASE_HEADERS,
            "Content-Type": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"'
        }
        data = {"@context": "https://www.w3.org/ns/activitystreams", **act}
        r = oauth.post(outbox_id, headers=headers, data=json.dumps(data))
        r.raise_for_status()
        return r.json()

    def text_prop(self, obj: dict, name: str) -> str:
        if name in obj:
            return obj[name]
        elif name + "Map" in obj:
            m = obj[name + "Map"]
            language_code = self.get_language_code()
            if language_code is None:
                raise Exception('No language code')
            if language_code in m:
                return m[language_code]
            elif "unk" in m:
                return m["unk"]
            else:
                return None
        else:
            return None

    def get_language_code(self) -> str:
        if not self._language_code:
            lang = self.env.get('LANG')
            if lang is None:
                raise Exception('No language code set')
            current_locale, _ = lang.split('.')
            if current_locale is None:
                raise Exception(f'No current_locale')
            self._language_code = current_locale[:2]
        return self._language_code

    def to_text(self, obj: dict) -> str:
        text = self.text_prop(obj, "name")
        if text is None:
            text = self.text_prop(obj, "summary")
        return text

    def get_actor_collection(self, prop: str) -> dict|str:
        actor = self.logged_in_actor()
        if prop not in actor:
            raise Exception("No " + prop + " found")
        return actor[prop]

    def get_endpoint(self, actor: dict, prop: str) -> str:
        if "endpoints" not in actor:
            raise Exception("No endpoints found")
        endpoints = actor["endpoints"]
        if type(endpoints) == str:
            # Technically allowed by AP spec
            endpoints = self.get_object(endpoints)
        if type(endpoints) != dict:
            raise Exception("Invalid endpoints")
        if prop not in endpoints:
            raise Exception("No " + prop + " found")
        return endpoints[prop]

    def collection_slice(self, coll: dict, offset: int, limit: int):
        return itertools.islice(self.items(coll), offset, offset + limit)

    def transform_microsyntax(self, source: str) -> tuple[str, list[dict[str, str]]]:
        html = escape(source)
        tag = []
        html, tag = self._replace_urls(html, tag)
        html, tag = self._replace_hashtags(html, tag)
        html, tag = self._replace_mentions(html, tag)
        html = f"<p>{html}</p>"
        return html, tag

    def _replace_urls(
        self, html: str, tag: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, str]]]:
        pattern = r"https?://\S+"
        segments = self._segment(html)
        for i, segment in enumerate(segments):
            if self._is_link(segment):
                continue
            segments[i] = re.sub(
                pattern, lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', segment
            )
        return "".join(segments), tag

    def _replace_hashtags(
        self, html: str, tag: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, str]]]:
        pattern = r"#(\w+)"
        segments = self._segment(html)

        def repl(m):
            logging.debug(m)
            name = m.group(1)
            href = self._tag_namespace + name
            tag.append({"type": "Hashtag", "name": m.group(0), "href": href})
            return f'<a href="{href}">{m.group(0)}</a>'

        for i, segment in enumerate(segments):
            if self._is_link(segment):
                continue
            segments[i] = re.sub(pattern, repl, segment)

        return "".join(segments), tag

    def _replace_mentions(
        self, html: str, tag: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, str]]]:

        pattern = r"@[a-zA-Z0-9_]+(?:[a-zA-Z0-9_.-]*[a-zA-Z0-9_]+)?@[a-zA-Z0-9_.-]+"

        def repl(m):
            match = m.group(0)
            # Remove the leading "@" for lookup.
            webfinger = match[1:]
            try:
                href = self._home_page(webfinger)
            except:
                return match
            if not href:
                return match
            tag.append({"type": "Mention", "name": match, "href": href})
            return f'<a href="{href}">{match}</a>'

        segments = self._segment(html)
        for i, segment in enumerate(segments):
            if self._is_link(segment):
                continue
            segments[i] = re.sub(pattern, repl, segment)
        return "".join(segments), tag

    def _is_link(self, segment: str):
        return (
            segment.startswith("<a>") or segment.startswith("<a ")
        ) and segment.endswith("</a>")

    def _segment(self, html: str):
        # Split the HTML while keeping HTML tag segments intact.
        pattern = r"(<[^>]+>[^<]+<\/[^>]+>)"
        return re.split(pattern, html)

    def _home_page(self, webfinger: str) -> str:
        url = self.to_webfinger_url(id)
        wf = webfinger.finger(url)
        profiles = [
            l["href"]
            for l in wf.links
            if l["rel"] == "http://webfinger.net/rel/profile-page"
        ]
        matches = [
            l["href"]
            for l in wf.links
            if l["rel"] == "self" and l["type"] == "application/activity+json"
        ]
        if len(matches) > 0:
            actor = self.get_object(matches[0])
            if actor is not None and actor["url"] is not None:
                return self._get_href(actor["url"])

        if len(profiles):
            return profiles[0]

        return None

    def _get_href(self, prop) -> str:
        if type(prop) == str:
            return prop
        elif type(prop) == dict:
            if "href" in prop:
                return prop["href"]
            else:
                return None
        elif type(prop) == list:
            if len(prop) > 0:
                return self._get_href(prop[0])
            else:
                return None
