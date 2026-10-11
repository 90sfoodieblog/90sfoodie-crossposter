#!/usr/bin/env python3
"""Thread scout — finds fresh 90s-snack Reddit threads for engagement.
READ-ONLY: writes candidates to thread_candidates.md, never posts."""
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import botlib

MIN_MEMBERS, MAX_MEMBERS = 22000, 50000
SEARCH_QUERIES = [
    "90s snacks", "90s candy", "90s cereal", "discontinued snacks",
    "90s chips", "90s soda", "childhood snacks",
]
SUBS_TO_SCAN = ["snacks", "90scereals", "nostalgia", "the90s", "forgottenfoods",
                "schoollunches", "junkfood", "candy"]


def get_json(url):
    req = urllib.request.Request(url, headers=botlib.UA)
    with urllib.request.urlopen(req, timeout=25) as r:
        import json
        return json.loads(r.read().decode())


def main():
    avoid = botlib.load_state("scout_avoid.json")
    avoid_subs = set(s.lower() for s in avoid.get("subs", []))
    avoid_topics = [t.lower() for t in avoid.get("topics", [])]
    avoid_urls = set(avoid.get("urls", []))

    sub_sizes = {}
    candidates = []
    seen = set()

    def sub_size(sub):
        s = sub.lower()
        if s not in sub_sizes:
            try:
                d = get_json(f"https://www.reddit.com/r/{s}/about.json")
                sub_sizes[s] = d["data"].get("subscribers", 0) or 0
            except Exception:
                sub_sizes[s] = 0
            time.sleep(1)
        return sub_sizes[s]

    def consider(d):
        pid = d.get("id")
        if not pid or pid in seen:
            return
        seen.add(pid)
        sub = d.get("subreddit", "")
        if sub.lower() in avoid_subs:
            return
        title = d.get("title", "")
        tl = title.lower()
        if any(t in tl for t in avoid_topics):
            return
        if d.get("stickied") or d.get("over_18"):
            return
        if (d.get("num_comments") or 0) < 5:
            return
        permalink = "https://www.reddit.com" + d.get("permalink", "")
        if permalink in avoid_urls:
            return
        size = sub_size(sub)
        if not (MIN_MEMBERS <= size <= MAX_MEMBERS):
            return
        candidates.append({
            "sub": sub, "size": size, "title": title,
            "url": permalink, "comments": d.get("num_comments", 0),
        })

    for q in SEARCH_QUERIES:
        try:
            url = "https://www.reddit.com/search.json?" + urllib.parse.urlencode(
                {"q": q, "sort": "new", "t": "week", "type": "link", "limit": 20})
            data = get_json(url)
            for child in data["data"]["children"]:
                consider(child["data"])
        except Exception as e:
            print(f"search failed ({q}): {e}")
        time.sleep(2)

    for sub in SUBS_TO_SCAN:
        try:
            data = get_json(f"https://www.reddit.com/r/{sub}/new.json?limit=25")
            for child in data["data"]["children"]:
                d = child["data"]
                tl = (d.get("title", "") + " " + d.get("selftext", "")).lower()
                if any(k in tl for k in ("90s", "90's", "nineties", "childhood", "discontinued", "retro")):
                    consider(d)
        except Exception as e:
            print(f"sub scan failed (r/{sub}): {e}")
        time.sleep(2)

    candidates.sort(key=lambda c: -c["comments"])
    top = candidates[:5]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    lines = [f"# Thread candidates — {today}", ""]
    if not top:
        lines.append("No matching threads found today.")
    for c in top:
        lines.append(f"## r/{c['sub']} ({c['size']:,} members, {c['comments']} comments)")
        lines.append(f"**{c['title']}**")
        lines.append(c["url"])
        lines.append("")
    with open("thread_candidates.md", "w") as f:
        f.write("\n".join(lines))
    print(f"Scout done: {len(top)} candidates written.")


if __name__ == "__main__":
    main()
