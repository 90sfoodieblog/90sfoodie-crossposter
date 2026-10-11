#!/usr/bin/env python3
"""Format-rotation bot — 2x daily, cycles formats so the feed never looks
samey: FACT -> QUESTION -> QUOTE -> MINI-THROWBACK. No two consecutive
runs use the same format."""
import random
from datetime import datetime, timezone

import botlib

FACTS = [
    "Dunkaroos were discontinued in the US in 2012 and brought back in 2020 after years of fan petitions.",
    "Crystal Pepsi was a clear cola launched in 1992 and pulled by 1994 — then revived briefly in 2016.",
    "French Toast Crunch was discontinued in the US in 2006, kept alive in Canada, and returned in 2015.",
    "Surge was Coca-Cola's answer to Mountain Dew, launched in 1996 with an extreme marketing blitz.",
    "Ecto Cooler was a Hi-C flavor tied to Ghostbusters that outlived the movies by decades.",
    "The white Shark Bite gummy was the rare one kids traded for in the 90s.",
    "Josta was the first energy drink brand in the US, launched by Pepsi in 1995.",
    "Orbitz soda had little floating balls suspended in the drink — it lasted about a year.",
    "Squeezit bottles had twist-off tops you were supposed to use as a straw hole.",
    "Oreo O's cereal was discontinued in the US in 2007 and brought back in 2017.",
    "3D Doritos launched in 1998 as puffed-up triangles in canisters.",
    "Cheetos Asteroids were tiny spherical Cheetos sold in canisters in the early 2000s.",
    "Lay's Crisps were the canister chips that later became Stax.",
    "Gushers launched in 1991 with the famous 'gusher' liquid center.",
    "Push Pops debuted in the mid-80s but peaked in the 90s lunchbox era.",
    "Baby Bottle Pop launched in 1998 — dip the rubber top, lick, repeat.",
    "Fun Dip's stick was originally called Lik-M-Aid when it launched.",
    "Pixy Stix started as a drink mix in the 1930s before becoming candy straws.",
    "Nerds were created in 1983 and became a 90s lunchbox staple.",
    "Warheads were imported from Taiwan and became the sour candy benchmark.",
    "Airheads launched in 1985 but hit peak playground status in the 90s.",
    "Tootsie Pops have been around since 1931 — the owl ad is from 1970.",
    "Blow Pops put gum inside a lollipop starting in the 1970s.",
    "Charleston Chews taste best frozen and smashed — a 90s kid discovery.",
    "Skittles' original lime flavor was replaced by green apple in 2013, then lime returned.",
    "Starburst were originally called Opal Fruits in the UK.",
    "Sour Patch Kids were first marketed as Mars Men in the 1970s.",
    "Fruit Roll-Ups launched in 1983 and owned the 90s lunchbox.",
    "Fruit by the Foot debuted in 1991 as a 3-foot-long snack.",
    "Lunchables launched in 1988 and defined 90s school lunches.",
    "Bagel Bites' famous jingle promised pizza any time of day.",
    "Totino's Pizza Rolls were invented in the early 90s.",
    "Hot Pockets launched in 1983 but became a 90s freezer icon.",
    "Cinnamon Toast Crunch's 'crazy squares' ads ran through the 90s.",
    "Lucky Charms added new marshmallow shapes every few years in the 90s.",
    "Trix lost its fruit shapes in 2006 and fans demanded them back for years.",
    "Cookie Crisp was reformulated multiple times — 90s kids remember the original.",
    "Golden Grahams were the base of every 90s s'mores bar recipe.",
    "Waffle Crisp cereal smelled like maple syrup straight from the box.",
    "Cap'n Crunch's full name is Horatio Magellan Crunch.",
    "Life cereal's 'Mikey likes it' ad is from the 1970s but ran for decades.",
    "Rice Krispies treats became a lunchbox staple in the 90s.",
    "Bugles were marketed as a 'fingertip' snack — everyone wore them as nails.",
    "Doritos were invented at Disneyland in the 1960s.",
    "Pringles' can was designed so the chips stack without breaking.",
    "Ruffles' ridges were literally engineered to hold more dip.",
    "Goldfish crackers were first made in Switzerland in 1958.",
    "Cheez-Its date back to 1921 — the 90s just perfected eating them.",
    "Smartfood popcorn launched in 1985 in the Boston area.",
    "Jiffy Pop's expanding foil pan was 90s stovetop theater.",
    "Kool-Aid Bursts' twist top was notoriously hard to open.",
    "Yoo-hoo was created in the 1920s but became a 90s lunchbox drink.",
    "Squeeze Pops were liquid candy you squeezed straight into your mouth.",
    "Ring Pops turned candy into playground jewelry.",
    "SweetTarts were invented in 1962 as a tart alternative to Pixy Stix.",
    "Runts' banana flavor tasted nothing like real bananas — and that was fine.",
    "Laffy Taffy jokes were groan-worthy and we read every one.",
    "Now and Later's name was the whole joke: eat some now, save some for later.",
    "Jolly Rancher's original flavors were watermelon, apple, and cherry.",
    "Milk Duds got their name because the machines couldn't make them perfectly round.",
    "Whoppers are malted milk balls first made in 1939.",
    "Junior Mints were named after the play 'Junior Miss'.",
]

QUESTIONS = [
    "Dunkaroos vs Gushers — you can only save one. Go.",
    "Best 90s cereal, no wrong answers (there are wrong answers): ___",
    "Push Pop or Ring Pop? Defend your choice.",
    "Was Crystal Pepsi actually good, or was it just the novelty?",
    "French Toast Crunch vs Cinnamon Toast Crunch — settle it.",
    "The white Shark Bite was the rare one. What was YOUR playground currency?",
    "Sour Patch Kids: team sour or team sweet?",
    "Best movie theater candy of the 90s? Wrong answers only... actually no, right answers.",
    "Lunchables pizza vs Lunchables nachos — which one raised you?",
    "Did anyone actually like the corn in Kid Cuisine? Be honest.",
    "Ecto Cooler: top-tier drink or overhyped green sugar water?",
    "Surge vs Mountain Dew in the 90s — who won?",
    "What 90s snack deserves a comeback the most?",
    "Fruit Roll-Ups or Fruit by the Foot? There is a correct answer.",
    "Were 3D Doritos better than regular Doritos? Discuss.",
    "Best chip for dip: Ruffles, Tostitos Scoops, or Fritos?",
    "Cheetos Asteroids — gone too soon or best forgotten?",
    "What did your 90s lunchbox always have in it?",
    "Soda of the 90s: Surge, Josta, Ecto Cooler, or Crystal Pepsi?",
    "Most underrated 90s candy? I will start: Charleston Chew, frozen.",
]

FORMATS = ["fact", "question", "quote", "mini-throwback"]


def main():
    state = botlib.load_state("formatrotation.json")
    last_format = state.get("last_format")
    choices = [f for f in FORMATS if f != last_format]
    fmt = random.choice(choices)
    print(f"Format-rotation: today's format is {fmt}")

    if fmt == "fact":
        idx = state.get("fact_idx", 0) % len(FACTS)
        text = f"📼 90s snack fact: {FACTS[idx]}"
        state["fact_idx"] = idx + 1
        botlib.post_bluesky_text(text)
        botlib.post_tumblr_html("90s snack fact",
                                f"<p>📼 <em>90s snack fact:</em></p>\n"
                                f"<p>{FACTS[idx]}</p>\n<p>The 90s Foodie</p>")

    elif fmt == "question":
        idx = state.get("q_idx", 0) % len(QUESTIONS)
        q = QUESTIONS[idx]
        state["q_idx"] = idx + 1
        botlib.post_bluesky_text(f"💬 {q}")
        botlib.post_tumblr_html("Question of the day",
                                f"<p>💬 <strong>{q}</strong></p>\n"
                                f"<p>Drop your answer below.</p>\n<p>The 90s Foodie</p>")

    elif fmt == "quote":
        try:
            posts = botlib.fetch_archive_posts(10)
        except Exception as e:
            print(f"Quote: archive failed ({e}), falling back to fact")
            fmt = "fact"
            idx = state.get("fact_idx", 0) % len(FACTS)
            state["fact_idx"] = idx + 1
            botlib.post_bluesky_text(f"📼 90s snack fact: {FACTS[idx]}")
            state["last_format"] = fmt
            botlib.save_state("formatrotation.json", state)
            return
        idx = state.get("quote_idx", 0) % len(posts)
        p = posts[idx]
        state["quote_idx"] = idx + 1
        line = (p.get("subtitle") or p.get("description") or p["title"]).strip()
        line = " ".join(line.split())
        if len(line) > 200:
            line = line[:197].rsplit(" ", 1)[0] + "..."
        text = f"💭 From the blog: “{line}”\n\n{p['url']}"
        if len(text) > 280:
            text = f"💭 From the blog\n\n{p['title']}\n\n{p['url']}"[:280]
        botlib.post_bluesky_text(text)
        botlib.post_tumblr_html(
            f"Quote: {p['title']}",
            f"<p>💭 <em>From the blog:</em></p>\n<blockquote>{line}</blockquote>\n"
            f"<p><a href=\"{p['url']}\">Read the article</a></p>")

    else:  # mini-throwback
        posted = botlib.load_state("posted.json")
        urls = list(posted.keys())
        if not urls:
            print("Mini-throwback: no posts available.")
            return
        idx = state.get("tb_idx", 0) % len(urls)
        url = urls[idx]
        state["tb_idx"] = idx + 1
        title = url.rstrip("/").split("/")[-1].replace("-", " ").title()
        text = f"🔁 From the archives: {title}\n\n{url}"
        if len(text) > 280:
            text = f"🔁 From the archives\n\n{title}\n\n{url}"[:280]
        botlib.post_bluesky_text(text)
        botlib.post_tumblr_html(
            f"Archives: {title}",
            f"<p>🔁 <em>From the archives.</em></p>\n"
            f"<p><a href=\"{url}\">{title}</a></p>\n<p>The 90s Foodie</p>")

    state["last_format"] = fmt
    botlib.save_state("formatrotation.json", state)
    print("Format-rotation done.")


if __name__ == "__main__":
    main()
