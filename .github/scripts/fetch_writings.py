#!/usr/bin/env python3
"""Fetch latest posts from a Substack RSS feed and write JSON to a file.

Only writes if at least one item is fetched, so a 403 / network failure
never overwrites a previously-good cache.

Usage: fetch_writings.py [output_path]
"""
import json
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://newontheblock.substack.com/feed"
LIMIT = 8
DEFAULT_OUTPUT = "writings.json"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)


def parse_items(root):
    items = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "Untitled").strip()
        link = (item.findtext("link") or "#").strip()
        pub = (item.findtext("pubDate") or "").strip()
        year = ""
        if pub:
            try:
                year = parsedate_to_datetime(pub).year
            except Exception:
                pass
        items.append({"title": title, "link": link, "year": year})
        if len(items) >= LIMIT:
            break
    return items


def try_fetch(url):
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        return parse_items(root)
    except Exception as exc:
        print(f"fetch_writings: {url} -> {exc}", file=sys.stderr)
        return []


def fetch():
    # Try the feed directly first; fall back to a CORS proxy if blocked.
    sources = [
        FEED,
        "https://api.allorigins.win/raw?url=" + urllib.parse.quote(FEED, safe=""),
    ]
    for url in sources:
        items = try_fetch(url)
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
