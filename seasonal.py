#!/usr/bin/env python3
"""Seasonal bot — daily check: matches old posts against seasonal windows
(Halloween, Christmas, summer, Super Bowl) and reshares the best fit.
Silent on days with no match."""
import random
from datetime import datetime, timezone

import botlib

# month-day windows: (name, (start_m, start_d), (end_m, end_d), keywords)
SEASONS = [
    ("Halloween", (10, 1), (10, 31),
     ["halloween", "candy", "chocolate", "gummy", "trick", "treat", "spooky",
      "caramel", "lollipop", "sour"]),
    ("Christmas", (12, 1), (12, 25),
     ["christmas", "holiday", "candy cane", "peppermint", "eggnog", "gingerbread",
      "cookie", "hot chocolate", "cocoa"]),
    ("Summer", (6, 1), (8, 31),
     ["summer", "ice cream", "popsicle", "freeze", "slush", "lemonade",
      "pool", "beach", "ottern pop", "bomb pop"]),
    ("Super Bowl", (1, 15), (2, 15),
     ["chip", "dip", "pizza", "wing", "nacho", "soda", "party", "game day",
      "doritos", "tostitos"]),
]


def in_window(now, start, end):
    md = (now.month, now.day)
    return start <= md <= end


def main():
    now = datetime.now(timezone.utc)
    active = [s for s in SEASONS if in_window(now, s[1], s[2])]
    if not active:
        print("Seasonal: no seasonal window today.")
        return
    name, _, _, keywords = active[0]
    posted = botlib.load_state("posted.json")
    state = botlib.load_state("seasonal.json")
    last = state.get(name, "")
    if last == now.strftime("%Y-%m"):
        print(f"Seasonal: already shared a {name} post this month.")
        return
    matches = [u for u in posted if any(k in u.lower() for k in keywords)]
    if not matches:
        print(f"Seasonal: no {name}-matching posts.")
        return
    url = random.choice(matches)
    title = url.rstrip("/").split("/")[-1].replace("-", " ").title()
    text = f"🎃 {name} season! Re-sharing: {title}\n\n{url}" if name == "Halloween" \
        else f"{name} season! Re-sharing: {title}\n\n{url}"
    if len(text) > 280:
        text = f"{name} season!\n\n{title}\n\n{url}"[:280]
    botlib.post_bluesky_text(text)
    botlib.post_tumblr_html(
        f"{name}: {title}",
        f"<p><em>Perfect for {name} season.</em></p>\n"
        f"<p><a href=\"{url}\">{title}</a></p>\n<p>The 90s Foodie</p>")
    state[name] = now.strftime("%Y-%m")
    botlib.save_state("seasonal.json", state)
    print(f"Seasonal done: {name} -> {title}")


if __name__ == "__main__":
    main()
