#!/usr/bin/env python3
"""Milestone bot — daily follower-threshold check.
Celebrates real milestones only. NEVER fakes a milestone."""
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

import botlib

MILESTONES = [50, 100, 250, 500, 1000, 2500, 5000, 10000]


def main():
    state = botlib.load_state("milestone.json")
    counts = {}

    # Bluesky public API
    try:
        handle = os.environ.get("BLUESKY_HANDLE", "90sfoodieblog.bsky.social")
        prof = botlib.http_get_json(
            "https://public.api.bsky.app/xrpc/app.bsky.actor.getProfile?"
            + urllib.parse.urlencode({"actor": handle}))
        counts["bluesky"] = prof.get("followersCount", 0)
    except Exception as e:
        print(f"Milestone: Bluesky count failed: {e}")

    # Tumblr authenticated
    try:
        creds = botlib._tumblr_creds()
        if not creds:
            raise RuntimeError("secrets missing")
        ck, cs, tok, ts, blog = creds
        url = f"https://api.tumblr.com/v2/blog/{blog}/info"
        auth = botlib._oauth1_header(url, {}, ck, cs, tok, ts, method="GET")
        req = urllib.request.Request(url, headers={"Authorization": auth})
        with urllib.request.urlopen(req, timeout=30) as r:
            import json
            info = json.loads(r.read().decode())["response"]["blog"]
        counts["tumblr"] = info.get("followers", 0)
    except Exception as e:
        print(f"Milestone: Tumblr count failed: {e}")

    celebrated = set(state.get("celebrated", []))
    changed = False
    for platform, n in counts.items():
        if not isinstance(n, int):
            continue
        for m in MILESTONES:
            key = f"{platform}:{m}"
            if n >= m and key not in celebrated:
                text = (f"🎉 Milestone! {m:,} followers on {platform.capitalize()} — "
                        f"thank you for loving 90s snacks with me. The 90s Foodie")
                botlib.post_bluesky_text(text)
                botlib.post_tumblr_html(
                    f"🎉 {m:,} followers on {platform.capitalize()}!",
                    f"<p>{text}</p>\n<p>The 90s Foodie</p>")
                celebrated.add(key)
                changed = True
                print(f"Milestone celebrated: {key}")
                break  # one celebration per platform per run
    if changed:
        state["celebrated"] = sorted(celebrated)
        state["last_check"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        botlib.save_state("milestone.json", state)
    else:
        print(f"Milestone: no new milestones (bluesky={counts.get('bluesky')}, "
              f"tumblr={counts.get('tumblr')}).")


if __name__ == "__main__":
    main()
