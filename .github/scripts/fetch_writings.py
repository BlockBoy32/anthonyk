#!/usr/bin/env python3
"""Fetch latest posts from a Substack RSS feed and write JSON to a file.

Substack returns 403 to datacenter IPs (including GitHub Actions runners), so
several routes are tried in order: the feed directly, Substack's archive JSON
API, then public read-through proxies. Proxies frequently truncate the
response, so a partial read is salvaged and parsed leniently rather than
discarded.

Only writes if at least one item is fetched, so a 403 / network failure
never overwrites a previously-good cache.

Usage: fetch_writings.py [output_path]
"""
import http.client
import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

HOST = "newontheblock.substack.com"
FEED = f"https://{HOST}/feed"
ARCHIVE = f"https://{HOST}/api/v1/archive?sort=new&limit=20"
RSS2JSON = "https://api.rss2json.com/v1/api.json?rss_url=" + urllib.parse.quote(
    FEED, safe=""
)
LIMIT = 8
DEFAULT_OUTPUT = "writings.json"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def year_of(pub):
    try:
        return parsedate_to_datetime(pub).year
    except Exception:
        return ""


def clean(text):
    """Strip CDATA wrappers and whitespace off a raw XML text node."""
    text = text.strip()
    m = re.fullmatch(r"<!\[CDATA\[(.*)\]\]>", text, re.S)
    return (m.group(1) if m else text).strip()


def parse_rss(data):
    """Parse an RSS document, falling back to regex if the XML is truncated."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        return parse_rss_partial(data)
    items = []
    for item in root.iter("item"):
        items.append(
            {
                "title": (item.findtext("title") or "Untitled").strip(),
                "link": (item.findtext("link") or "#").strip(),
                "year": year_of((item.findtext("pubDate") or "").strip()),
            }
        )
        if len(items) >= LIMIT:
            break
    return items


def parse_rss_partial(data):
    """Recover whole <item> blocks from a truncated feed."""
    text = data.decode("utf-8", "replace")
    items = []
    for block in re.findall(r"<item[^>]*>(.*?)</item>", text, re.S):
        def field(name):
            m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", block, re.S)
            return clean(m.group(1)) if m else ""

        title = field("title") or "Untitled"
        link = field("link") or "#"
        items.append({"title": title, "link": link, "year": year_of(field("pubDate"))})
        if len(items) >= LIMIT:
            break
    return items


def parse_archive(data):
    """Parse Substack's archive JSON API."""
    posts = json.loads(data.decode("utf-8", "replace"))
    items = []
    for post in posts:
        date = (post.get("post_date") or "")[:4]
        items.append(
            {
                "title": (post.get("title") or "Untitled").strip(),
                "link": post.get("canonical_url") or "#",
                "year": int(date) if date.isdigit() else "",
            }
        )
        if len(items) >= LIMIT:
            break
    return items


def parse_rss2json(data):
    """Parse rss2json, which fetches the feed from its own servers."""
    payload = json.loads(data.decode("utf-8", "replace"))
    if payload.get("status") != "ok":
        raise ValueError(payload.get("message") or "rss2json returned an error")
    items = []
    for post in payload.get("items", []):
        date = (post.get("pubDate") or "")[:4]
        items.append(
            {
                "title": (post.get("title") or "Untitled").strip(),
                "link": (post.get("link") or "#").strip(),
                "year": int(date) if date.isdigit() else "",
            }
        )
        if len(items) >= LIMIT:
            break
    return items


def proxied(url):
    quoted = urllib.parse.quote(url, safe="")
    return [
        "https://api.allorigins.win/raw?url=" + quoted,
        "https://api.codetabs.com/v1/proxy?quest=" + quoted,
        "https://corsproxy.io/?url=" + quoted,
        "https://thingproxy.freeboard.io/fetch/" + url,
    ]


def try_fetch(url, parse):
    """Fetch one URL, salvaging a truncated body rather than discarding it."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/xml, text/xml, application/json, */*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = resp.read()
        except http.client.IncompleteRead as exc:
            data = exc.partial
            print(
                f"fetch_writings: {url} -> truncated, salvaging {len(data)} bytes",
                file=sys.stderr,
            )
        return parse(data)
    except Exception as exc:
        print(f"fetch_writings: {url} -> {exc}", file=sys.stderr)
        return []


def fetch():
    sources = [(FEED, parse_rss), (ARCHIVE, parse_archive), (RSS2JSON, parse_rss2json)]
    sources += [(u, parse_rss) for u in proxied(FEED)]
    sources += [(u, parse_archive) for u in proxied(ARCHIVE)]
    for url, parse in sources:
        items = try_fetch(url, parse)
        if items:
            print(f"fetch_writings: got {len(items)} items from {url}", file=sys.stderr)
            return items
    return []


def main():
    output_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUTPUT
    items = fetch()
    if not items:
        print(
            f"fetch_writings: no items; leaving {output_path} unchanged",
            file=sys.stderr,
        )
        return 0
    with open(output_path, "w") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"fetch_writings: wrote {len(items)} items to {output_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
