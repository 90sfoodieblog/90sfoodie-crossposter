#!/usr/bin/env python3
"""Second-wave bot — evening reshare of articles published in the last 14 hours.
Runs daily in the evening. Each article gets exactly one second wave."""
import random
from datetime import datetime, timezone

import botlib

WINDOW_HOURS = 14
INTROS = [
    "In case you missed it earlier",
    "Evening rewind",
    "One more time for the night crowd",
]


def main():
    state = botlib.load_state("secondwave.json")
    try:
        posts = botlib.fetch_archive_posts(10)
    except Exception as e:
        print(f"Second-wave: archive fetch failed: {e}")
        return
    now = datetime.now(timezone.utc)
    done_any = False
    for p in posts:
        url = p["url"]
        if url in state:
            continue
        try:
            age_h = (now - datetime.fromisoformat(
                p["post_date"].replace("Z", "+00:00"))).total_seconds() / 3600
        except (ValueError, KeyError):
            continue
        if age_h > WINDOW_HOURS:
            state[url] = "skipped"
            continue
        intro = random.choice(INTROS)
        bsky_text = f"{intro}: {p['title']}\n\n{url}"
        if len(bsky_text) > 280:
            bsky_text = f"{intro}\n\n{p['title']}\n\n{url}"[:280]
        botlib.post_bluesky_text(bsky_text)
        botlib.post_tumblr_html(
            p["title"],
            f"<p><em>{intro}.</em></p>\n"
            f"<p><a href=\"{url}\">{p['title']}</a></p>\n<p>The 90s Foodie</p>")
        state[url] = now.strftime("%Y-%m-%d")
        done_any = True
        print(f"Second-wave done: {p['title']}")
    botlib.save_state("secondwave.json", state)
    if not done_any:
        print("Second-wave: nothing in the 14-hour window.")


if __name__ == "__main__":
    main()
