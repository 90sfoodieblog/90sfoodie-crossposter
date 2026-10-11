#!/usr/bin/env python3
"""Idea bank — collects trending 90s-snack topics weekly.
READ-ONLY: writes idea_bank.md, never posts."""
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import botlib

SUBS = ["snacks", "90scereals", "nostalgia", "the90s"]
NEWS_QUERIES = ["discontinued snack", "90s snack", "retro candy", "throwback cereal"]
KEYWORDS = ["90s", "90's", "nineties", "childhood", "discontinued", "retro",
            "throwback", "remember", "forgotten", "bring back"]


def get_json(url):
    req = urllib.request.Request(url, headers=botlib.UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        import json
        return json.loads(r.read().decode())


def main():
    ideas = []

    for sub in SUBS:
        try:
            data = get_json(f"https://www.reddit.com/r/{sub}/hot.json?limit=25")
            for child in data["data"]["children"]:
                d = child["data"]
                tl = (d.get("title", "") + " " + d.get("selftext", "")).lower()
                if any(k in tl for k in KEYWORDS) and not d.get("stickied"):
                    ideas.append({
                        "source": f"r/{sub}",
                        "title": d.get("title", ""),
                        "url": "https://www.reddit.com" + d.get("permalink", ""),
                        "heat": d.get("ups", 0),
                        "why": f"{d.get('ups', 0)} upvotes, {d.get('num_comments', 0)} comments on r/{sub}",
                    })
        except Exception as e:
            print(f"r/{sub} failed: {e}")
        time.sleep(2)

    for q in NEWS_QUERIES:
        try:
            url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
                {"q": q, "hl": "en-US", "gl": "US", "ceid": "US:en"})
            req = urllib.request.Request(url, headers=botlib.UA)
            with urllib.request.urlopen(req, timeout=25) as r:
                root = ET.fromstring(r.read())
            for item in root.iter("item")[:10]:
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                if title and any(k in title.lower() for k in KEYWORDS):
                    ideas.append({
                        "source": "google-news", "title": title, "url": link,
                        "heat": 0, "why": f"News hit for '{q}'",
                    })
        except Exception as e:
            print(f"news query failed ({q}): {e}")
        time.sleep(2)

    # Dedupe against covered topics and previous bank entries
    posted = botlib.load_state("posted.json")
    covered = " ".join(posted.keys()).lower()
    prev_bank = ""
    try:
        with open("idea_bank.md") as f:
            prev_bank = f.read().lower()
    except OSError:
        pass
    seen_titles, fresh = set(), []
    for i in ideas:
        t = i["title"].strip()
        tl = t.lower()
        if not t or tl in seen_titles:
            continue
        seen_titles.add(tl)
        words = [w for w in tl.split() if len(w) > 4]
        if any(w in covered for w in words[:3]) or tl in prev_bank:
            continue
        fresh.append(i)
    fresh.sort(key=lambda i: -i["heat"])

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# Idea bank — {today}", ""]
    if not fresh:
        lines.append("No fresh ideas this week.")
    for i in fresh[:10]:
        lines.append(f"## {i['title']}")
        lines.append(f"- Source: {i['source']} — {i['why']}")
        lines.append(f"- {i['url']}")
        lines.append("")
    with open("idea_bank.md", "w") as f:
        f.write("\n".join(lines))
    print(f"Idea bank done: {min(len(fresh), 10)} ideas written.")


if __name__ == "__main__":
    main()
