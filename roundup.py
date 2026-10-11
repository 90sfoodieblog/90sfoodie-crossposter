#!/usr/bin/env python3
"""Weekend roundup bot — Sunday digest of articles published in the
last 14 days. Posts a Bluesky thread + a Tumblr digest."""
from datetime import datetime, timezone

import botlib

WINDOW_DAYS = 14


def main():
    state = botlib.load_state("roundup.json")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_date") == today:
        print("Roundup: already ran today.")
        return
    try:
        posts = botlib.fetch_archive_posts(20)
    except Exception as e:
        print(f"Roundup: archive fetch failed: {e}")
        return
    now = datetime.now(timezone.utc)
    recent = []
    for p in posts:
        try:
            age = (now - datetime.fromisoformat(
                p["post_date"].replace("Z", "+00:00"))).days
        except (ValueError, KeyError):
            continue
        if age <= WINDOW_DAYS:
            recent.append(p)
    if not recent:
        print("Roundup: nothing published in the last 14 days.")
        return

    thread = [f"📰 The 90s Foodie weekend roundup — {len(recent)} fresh from the vault:"]
    for p in recent[:5]:
        line = f"• {p['title']}\n{p['url']}"
        thread.append(line if len(line) <= 275 else line[:272] + "...")
    botlib.post_bluesky_thread(thread)

    items = "".join(
        f"<li><a href=\"{p['url']}\">{p['title']}</a></li>" for p in recent[:10])
    botlib.post_tumblr_html(
        f"Weekend roundup — {today}",
        f"<p>Everything from the last two weeks on The 90s Foodie:</p>\n"
        f"<ul>{items}</ul>\n<p>The 90s Foodie</p>")

    state["last_date"] = today
    botlib.save_state("roundup.json", state)
    print(f"Roundup done: {len(recent)} posts.")


if __name__ == "__main__":
    main()
