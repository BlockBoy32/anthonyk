#!/usr/bin/env python3
"""Fetch latest posts from a Substack RSS feed and emit JSON to stdout."""
import json
import sys
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

FEED = "https://newontheblock.substack.com/feed"
LIMIT = 8


def main() -> int:
    try:
        req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        root = ET.fromstring(data)
    except Exception as exc:
        print(f"fetch_writings: failed to fetch feed: {exc}", file=sys.stderr)
        sys.stdout.write("[]\n")
        return 0

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
                year = ""
        items.append({"title": title, "link": link, "year": year})
        if len(items) >= LIMIT:
            break

    json.dump(items, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
