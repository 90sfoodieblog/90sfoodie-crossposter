#!/usr/bin/env python3
"""Snack-news watcher — daily conservative scan of Google News RSS and
Reddit for clearly relevant snack-product news. Max 2 flashes per day."""
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import botlib

QUERIES = ["discontinued snack returns", "90s snack comeback",
           "retro candy relaunch", "throwback cereal"]
SUBS = ["snacks", "junkfood"]
MAX_PER_DAY = 2
# Conservative relevance: must mention a snack product term AND a newsy term
PRODUCT = re.compile(r"(cereal|candy|chip|soda|cookie|gum|snack|pop|bar|drink)", re.I)
NEWSY = re.compile(r"(return|comeback|relaunch|bring back|discontinued|limited edition|"
                   r"announce|new flavor|90s|retro|throwback)", re.I)


def main():
    state = botlib.load_state("snackwatch.json")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posted_today = state.get(today, [])
    if len(posted_today) >= MAX_PER_DAY:
        print("Snack-news: daily cap reached.")
        return
    hits = []

    def relevant(title):
        return bool(PRODUCT.search(title) and NEWSY.search(title))

    for q in QUERIES:
        try:
            url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
                {"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"})
            req = urllib.request.Request(url, headers=botlib.UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                root = ET.fromstring(r.read())
            for item in root.iter("item")[:15]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if title and relevant(title) and link not in posted_today:
                    hits.append({"title": title, "url": link, "src": "news"})
        except Exception as e:
            print(f"news query failed ({q}): {e}")
        time.sleep(2)

    for sub in SUBS:
        try:
            req = urllib.request.Request(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=20", headers=botlib.UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                import json
                data = json.loads(r.read().decode())
            for child in data["data"]["children"]:
                d = child["data"]
                title = d.get("title", "")
                plink = "https://www.reddit.com" + d.get("permalink", "")
                if relevant(title) and plink not in posted_today and not d.get("stickied"):
                    hits.append({"title": title, "url": plink, "src": f"r/{sub}"})
        except Exception as e:
            print(f"r/{sub} failed: {e}")
        time.sleep(2)

    seen, fresh = set(), []
    for h in hits:
        tl = h["title"].lower()
        if tl not in seen:
            seen.add(tl)
            fresh.append(h)
    if not fresh:
        print("Snack-news: nothing clearly relevant today.")
        return
    for h in fresh[: MAX_PER_DAY - len(posted_today)]:
        text = f"📣 Snack news: {h['title']}\n\n{h['url']}"
        if len(text) > 280:
            text = f"📣 Snack news\n\n{h['title'][:180]}...\n\n{h['url']}"[:280]
        botlib.post_bluesky_text(text)
        botlib.post_tumblr_html(
            f"Snack news: {h['title'][:80]}",
            f"<p>📣 Via {h['src']}:</p>\n<p><a href=\"{h['url']}\">{h['title']}</a></p>\n"
            "<p>The 90s Foodie</p>")
        posted_today.append(h["url"])
        print(f"Snack-news flash: {h['title'][:60]}")
    state[today] = posted_today
    botlib.save_state("snackwatch.json", state)


if __name__ == "__main__":
    main()
