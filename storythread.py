#!/usr/bin/env python3
"""Story-thread bot — weekly: Bluesky reply-chain (4 posts) + one long
Tumblr post telling a 90s snack story drawn from a blog article."""
import random
from datetime import datetime, timezone

import botlib

STORY_LEADS = [
    "Story time from the 90s snack vault",
    "Let me tell you about a snack that ruled the 90s",
]


def sentences_from_post(post):
    """Pull a few plain sentences from the article body for the story."""
    text = botlib.strip_html(post.get("body_html", ""))
    sents = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".")
             if len(s.strip()) > 40]
    return sents[:8]


def main():
    state = botlib.load_state("storythread.json")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if state.get("last_date") == today:
        print("Story-thread: already ran today.")
        return
    try:
        posts = botlib.fetch_archive_posts(15)
    except Exception as e:
        print(f"Story-thread: archive fetch failed: {e}")
        return
    used = set(state.get("used_urls", []))
    pool = [p for p in posts if p["url"] not in used] or posts
    p = random.choice(pool)
    sents = sentences_from_post(p)
    if not sents:
        sents = [f"{p['title']} — one of the defining snacks of the decade."]
    lead = random.choice(STORY_LEADS)
    thread = [f"{lead}: {p['title']}"]
    for s in sents[:3]:
        thread.append(s if len(s) <= 275 else s[:272] + "...")
    thread.append(f"Full story on the blog:\n\n{p['url']}")
    botlib.post_bluesky_thread(thread)

    body = (f"<p><em>{lead}.</em></p>\n"
            f"<h3>{p['title']}</h3>\n"
            + "".join(f"<p>{s}.</p>" for s in sents[:6])
            + f"<p><a href=\"{p['url']}\">Read the full article</a></p>\n"
              "<p>The 90s Foodie</p>")
    botlib.post_tumblr_html(f"Story: {p['title']}", body)

    state["last_date"] = today
    used.add(p["url"])
    state["used_urls"] = sorted(used)[-30:]
    botlib.save_state("storythread.json", state)
    print(f"Story-thread done: {p['title']}")


if __name__ == "__main__":
    main()
