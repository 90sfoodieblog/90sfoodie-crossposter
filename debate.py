#!/usr/bin/env python3
"""Debate bot — Mon/Fri discussion question based on the latest article.
Posts a question + link to spark comments."""
import random
from datetime import datetime, timezone

import botlib

QUESTION_TEMPLATES = [
    "Settle it: which was better — {a} or {b}?",
    "Hot take time: {title} — agree or disagree?",
    "Quick poll: {title} — what is your pick?",
    "Debate below: {title} — change my mind.",
]


def main():
    state = botlib.load_state("debate.json")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        posts = botlib.fetch_archive_posts(5)
    except Exception as e:
        print(f"Debate: archive fetch failed: {e}")
        return
    if not posts:
        print("Debate: no posts found.")
        return
    p = posts[0]
    if state.get("last_url") == p["url"] and state.get("last_date") == today:
        print("Debate: already asked today.")
        return
    words = [w.strip(".,!?\"'") for w in p["title"].split()]
    nouns = [w for w in words if len(w) > 3][:6]
    if len(nouns) >= 2:
        q = QUESTION_TEMPLATES[0].format(a=nouns[0], b=nouns[1])
    else:
        q = random.choice(QUESTION_TEMPLATES[1:]).format(title=p["title"])
    bsky_text = f"{q}\n\n{p['url']}"
    if len(bsky_text) > 280:
        bsky_text = f"{q[:200]}...\n\n{p['url']}"[:280]
    botlib.post_bluesky_text(bsky_text)
    botlib.post_tumblr_html(
        f"Debate: {p['title']}",
        f"<p><strong>{q}</strong></p>\n"
        f"<p>From <a href=\"{p['url']}\">{p['title']}</a> — drop your take below.</p>")
    state["last_url"] = p["url"]
    state["last_date"] = today
    botlib.save_state("debate.json", state)
    print(f"Debate done: {q[:60]}")


if __name__ == "__main__":
    main()
