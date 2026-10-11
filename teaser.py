#!/usr/bin/env python3
"""Teaser bot — Wed/Sun teaser from the latest article.
Posts a hook line + link. Never reveals the whole article."""
import random
from datetime import datetime, timezone

import botlib

TEASER_LEADS = [
    "Coming up on the blog",
    "Fresh from the 90s vault",
    "New post just dropped",
]


def pick_hook(post):
    """Build a teaser line from subtitle/description without spoiling."""
    cand = post.get("subtitle") or post.get("description") or ""
    cand = " ".join(cand.split())
    if len(cand) > 160:
        cut = cand[:160].rsplit(" ", 1)[0]
        return cut + "..."
    return cand or "You are not ready for this one."


def main():
    state = botlib.load_state("teaser.json")
    try:
        posts = botlib.fetch_archive_posts(5)
    except Exception as e:
        print(f"Teaser: archive fetch failed: {e}")
        return
    if not posts:
        print("Teaser: no posts found.")
        return
    p = posts[0]
    if state.get("last_url") == p["url"] and state.get("last_date") == \
            datetime.now(timezone.utc).strftime("%Y-%m-%d"):
        print("Teaser: already teased today.")
        return
    lead = random.choice(TEASER_LEADS)
    hook = pick_hook(p)
    bsky_text = f"{lead}: {hook}\n\n{p['url']}"
    if len(bsky_text) > 280:
        bsky_text = f"{lead}\n\n{p['title']}\n\n{p['url']}"[:280]
    botlib.post_bluesky_text(bsky_text)
    botlib.post_tumblr_html(
        f"Teaser: {p['title']}",
        f"<p><em>{lead}.</em></p>\n<p>{hook}</p>\n"
        f"<p><a href=\"{p['url']}\">Read it on the blog</a></p>")
    state["last_url"] = p["url"]
    state["last_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    botlib.save_state("teaser.json", state)
    print(f"Teaser done: {p['title']}")


if __name__ == "__main__":
    main()
