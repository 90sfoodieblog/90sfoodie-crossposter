#!/usr/bin/env python3
"""Stats collector — snapshots Bluesky + Tumblr stats daily.
READ-ONLY: appends to stats_history.json, never posts."""
import os
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import botlib

HANDLE = os.environ.get("BLUESKY_HANDLE", "90sfoodieblog.bsky.social")


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = {"date": today}

    # Bluesky (public API, no auth)
    try:
        prof = botlib.http_get_json(
            "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?"
            + urllib.parse.urlencode({"actor": HANDLE}))
        entry["bsky_followers"] = prof.get("followersCount")
        entry["bsky_follows"] = prof.get("followsCount")
        entry["bsky_posts"] = prof.get("postsCount")
        feed = botlib.http_get_json(
            "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed?"
            + urllib.parse.urlencode({"actor": HANDLE, "limit": 5}))
        top = []
        for item in feed.get("feed", [])[:5]:
            p = item["post"]
            top.append({
                "text": (p["record"].get("text", "")[:60]),
                "likes": p.get("likeCount", 0),
                "reposts": p.get("repostCount", 0),
                "replies": p.get("replyCount", 0),
            })
        entry["bsky_top_posts"] = top
        print("Bluesky stats OK")
    except Exception as e:
        entry["bsky_error"] = str(e)[:120]
        print(f"Bluesky stats failed: {e}")

    # Tumblr (authenticated)
    try:
        creds = botlib._tumblr_creds()
        if not creds:
            raise RuntimeError("secrets missing")
        ck, cs, tok, ts, blog = creds
        url = f"https://api.tumblr.com/v2/blog/{blog}/info"
        auth = botlib._oauth1_header(url, {}, ck, cs, tok, ts)
        req = urllib.request.Request(url, headers={"Authorization": auth})
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            info = json.loads(r.read().decode())["response"]["blog"]
        entry["tumblr_followers"] = info.get("followers")
        entry["tumblr_posts"] = info.get("posts")
        entry["tumblr_likes"] = info.get("likes")
        print("Tumblr stats OK")
    except Exception as e:
        entry["tumblr_error"] = str(e)[:120]
        print(f"Tumblr stats failed: {e}")

    hist = botlib.load_state("stats_history.json")
    if not isinstance(hist, list):
        hist = []
    hist = [h for h in hist if h.get("date") != today]
    hist.append(entry)
    botlib.save_state("stats_history.json", hist)
    print(f"Stats saved for {today}.")


if __name__ == "__main__":
    main()
