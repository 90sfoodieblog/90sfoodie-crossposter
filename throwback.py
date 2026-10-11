#!/usr/bin/env python3
"""Throwback bot — reshares older posts to Bluesky + Tumblr.
Skips anything re-shared in the last 60 days and anything
published in the last 90 days. Runs Tue/Thu/Sat mornings."""
import random
from datetime import datetime, timezone

import botlib

COOLDOWN_DAYS = 60
NEW_POST_GRACE_DAYS = 90
INTROS = [
    "Throwback to this one",
    "From the archives",
    "Still thinking about this",
    "A classic from the blog",
    "Worth another look",
]


def main():
    posted = botlib.load_state("posted.json")
    if not posted:
        print("Throwback: no posts in posted.json")
        return
    state = botlib.load_state("throwback.json")
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")

    eligible = []
    for url in posted:
        last = state.get(url, "")
        if last:
            try:
                days = (now - datetime.strptime(last, "%Y-%m-%d").replace(
                    tzinfo=timezone.utc)).days
            except ValueError:
                days = 999
            if days < COOLDOWN_DAYS:
                continue
        eligible.append(url)
    # Exclude posts published in the last 90 days (pull dates from archive)
    try:
        posts = botlib.fetch_archive_posts(20)
        fresh = {p["url"] for p in posts
                 if p["post_date"] and (now - datetime.fromisoformat(
                     p["post_date"].replace("Z", "+00:00"))).days < NEW_POST_GRACE_DAYS}
        titles = {p["url"]: p["title"] for p in posts}
    except Exception as e:
        print(f"Throwback: archive fetch failed ({e}), using posted.json only")
        fresh, titles = set(), {}
    eligible = [u for u in eligible if u not in fresh]
    if not eligible:
        print("Throwback: nothing eligible today.")
        return

    url = random.choice(eligible)
    title = titles.get(url, url.rstrip("/").split("/")[-1].replace("-", " ").title())
    intro = random.choice(INTROS)
    bsky_text = f"{intro}: {title}\n\n{url}"
    if len(bsky_text) > 280:
        bsky_text = f"{intro}\n\n{title}\n\n{url}"[:280]
    tumblr_body = (f'<p><em>{intro}.</em></p>\n'
                   f'<p><a href="{url}">{title}</a></p>\n<p>The 90s Foodie</p>')

    botlib.post_bluesky_text(bsky_text)
    botlib.post_tumblr_html(f"Throwback: {title}", tumblr_body)
    state[url] = today
    botlib.save_state("throwback.json", state)
    print(f"Throwback done: {title}")


if __name__ == "__main__":
    main()
