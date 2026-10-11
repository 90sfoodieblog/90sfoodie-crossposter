#!/usr/bin/env python3
"""Snack o'clock bot — 3x daily snack spotlight (10am / 3pm / 8pm CT).
Rotates through a bank of 90 snacks with a vivid memory line each."""
import random
from datetime import datetime, timezone

import botlib

BANK = [
    ("Dunkaroos", "Frosting for dipping. The 90s knew exactly what kids wanted."),
    ("Gushers", "Bite it and it gushes. Fruit snacks peaked right here."),
    ("Push Pop", "Candy you could save for later — if you had the willpower."),
    ("Warheads", "The sour challenge before sour was a whole genre."),
    ("Ecto Cooler", "Hi-C's green ghost drink. Slimer would approve."),
    ("Surge", "Fully loaded citrus chaos in a can."),
    ("Crystal Pepsi", "Clear cola. It tasted like the future, briefly."),
    ("Josta", "The first energy drink most of us ever tried."),
    ("Orbitz", "Soda with floating balls in it. Nobody asked, everybody drank."),
    ("Squeezit", "Twist the top, squeeze the bottle, pure 90s."),
    ("Kool-Aid Bursts", "The bottle with the twisty top that never worked right."),
    ("Yoo-hoo", "Chocolate drink that somehow was not chocolate milk."),
    ("Squeeze Pops", "Liquid candy in a tube. Sticky fingers guaranteed."),
    ("Baby Bottle Pop", "Dip the rubber nipple, lick, repeat."),
    ("Ring Pop", "Jewelry you could eat. Peak playground currency."),
    ("Lick-A-Stix", "Wait — no, that is the other one. Anyway: pure sugar."),
    ("Fun Dip", "A stick of chalky candy and a pouch of flavored sugar."),
    ("Pixy Stix", "Paper straws of pure sugar. The original energy drink."),
    ("Nerds", "Two flavors in one box, tiny crunchy chaos."),
    ("Runts", "Banana ones tasted like nothing on earth. Perfect."),
    ("SweetTarts", "Sour then sweet. The tagline wrote itself."),
    ("Smarties", "Canadian Smarties are chocolate. American Smarties are chalk. Both rule."),
    ("Airheads", "Stretchy, chewy, mysteriously flavored."),
    ("Laffy Taffy", "Jokes on the wrapper. The banana one was elite."),
    ("Now and Later", "Chewy enough to last the whole bus ride."),
    ("Jolly Rancher", "Watermelon was the one everyone fought over."),
    ("Tootsie Pop", "How many licks? The owl never told us."),
    ("Blow Pop", "Gum in the middle. Two treats, one stick."),
    ("Charleston Chew", "Freeze it, smack it, shatter it. Science."),
    ("Milk Duds", "They melt in your mouth, not in your hand — mostly."),
    ("Whoppers", "Malted milk balls. Movie theater essential."),
    ("Raisinets", "The 'healthy' movie candy. Sure."),
    ("Sno-Caps", "Tiny chocolate nonpareils. Crunchy little snowmen."),
    ("Junior Mints", "Cool, refreshing, and somehow always at the movies."),
    ("Skittles", "Taste the rainbow. The lime one was the best green."),
    ("Starburst", "Unwrap the pink one first. Always."),
    ("Twizzlers", "Strawberry twists > everything. Also great as straws."),
    ("Red Vines", "The Twizzlers rival. Pick a side."),
    ("Sour Patch Kids", "First they are sour, then they are sweet."),
    ("Swedish Fish", "Chewy, red, fish-shaped. No notes."),
    ("Gummy Bears", "Haribo goldbears. The pineapple one was gold."),
    ("Gummy Worms", "Sour ones made your face do things."),
    ("Fruit Roll-Ups", "Peel it, stick tattoos on your tongue, eat it."),
    ("Fruit by the Foot", "Three feet of fun. Measure twice, eat once."),
    ("Shark Bites", "The white shark was the rare one. Playground legend."),
    ("Scooby-Doo Gummies", "The opaque ones tasted better. Science can't explain."),
    ("Betty Crocker Fruit Snacks", "The whole genre in one purple box."),
    ("Handi-Snacks", "Cheese and crackers with a red stick. DIY lunch."),
    ("Lunchables", "The pizza one with the little red stick. Elite."),
    ("Dunkin' Stix", "Breadsticks and cheese sauce. Fancy Lunchables."),
    ("Kid Cuisine", "The penguin, the brownie, the corn that nobody ate."),
    ("Bagel Bites", "Pizza in the morning, pizza in the evening..."),
    ("Pizza Rolls", "Totino's. Lava-hot centers, always."),
    ("Hot Pockets", "Hotter than the sun. Wait two minutes. Still burn your mouth."),
    ("French Toast Crunch", "Tiny toast you could eat with a spoon. Genius."),
    ("Cinnamon Toast Crunch", "The milk at the end was the real prize."),
    ("Lucky Charms", "Marshmallow shapes > toasted oats. Fight me."),
    ("Trix", "Silly rabbit. The shapes came back and we celebrated."),
    ("Cocoa Puffs", "Chocolate milk as a side effect of breakfast."),
    ("Reese's Puffs", "Candy for breakfast. No regrets."),
    ("Cookie Crisp", "Cookies for breakfast. The 90s had no rules."),
    ("Golden Grahams", "S'mores cereal. The marshmallow hunt was real."),
    ("S'mores Crunch", "Gone too soon. We still talk about it."),
    ("Waffle Crisp", "Tasted like syrup. The box smelled like victory."),
    ("Oreo O's", "Cookies and milk, already combined. Efficient."),
    ("Frosted Flakes", "More than good — they were gr-r-reat."),
    ("Froot Loops", "Follow your nose. Toucan Sam knew."),
    ("Apple Jacks", "They don't taste like apples. We didn't care."),
    ("Cap'n Crunch", "Roof-of-mouth destroyer. Worth it every time."),
    ("Crunch Berries", "Turned the milk an unnatural color. Beautiful."),
    ("Life Cereal", "Mikey likes it. So did we."),
    ("Cheerios", "The plain one nobody picked first. Respect anyway."),
    ("Honey Nut Cheerios", "The bee said it was part of a complete breakfast."),
    ("Rice Krispies", "Snap, crackle, pop. Then marshmallows happened."),
    ("Corn Pops", "Sweet, crunchy, oddly puffy."),
    ("Kix", "Kid-tested, mother-approved. The slogan stuck."),
    ("Chex Mix", "The bag never survived the car ride home."),
    ("Bugles", "Put them on your fingertips like witch nails."),
    ("Doritos 3D", "Puffy triangles. The canister era was elite."),
    ("Cheetos Asteroids", "Tiny crunchy meteors from the snack canister."),
    ("Lay's Crisps", "The canister chips. Stax before Stax."),
    ("Pringles", "Once you pop... the can was the whole point."),
    ("Ruffles", "Ridges for the dip. Engineering at its finest."),
    ("Fritos", "Scoops were built for chili cheese dip."),
    ("Tostitos", "Party in a bag. The 90s invented the dip era."),
    ("SunChips", "The 'healthy' chip. The garden salsa one slapped."),
    ("Pita chips", "Okay these were more late 90s. Still counts."),
    ("Combos", "Cheese-filled pretzel tubes. Gas station royalty."),
    ("Goldfish", "The snack that smiles back."),
    ("Cheez-Its", "Baked, not fried. Dangerously poppable."),
    ("Cheese Nips", "The Cheez-It rival. Pick your fighter."),
    ("Pretzel rods", "For building log cabins and also eating."),
    ("Rold Gold", "Tiny pretzels. The twist ones were best."),
    ("Popcorn", "Jiffy Pop on the stove. The foil dome was magic."),
    ("Smartfood", "White cheddar popcorn. The black bag meant business."),
]


def main():
    state = botlib.load_state("snackoclock.json")
    idx = state.get("index", 0) % len(BANK)
    snack, line = BANK[idx]
    hour = datetime.now(timezone.utc).hour - 5  # approx CT
    slot = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening"
    text = f"🕙 Snack o'clock ({slot} edition)\n\n{snack}: {line}\n\nWhat is your {snack} memory?"
    if len(text) > 280:
        text = f"🕙 Snack o'clock: {snack}\n\n{line}"[:280]
    botlib.post_bluesky_text(text)
    botlib.post_tumblr_html(
        f"Snack o'clock: {snack}",
        f"<p>🕙 <em>Snack o'clock — {slot} edition.</em></p>\n"
        f"<p><strong>{snack}:</strong> {line}</p>\n"
        f"<p>What is your {snack} memory?</p>\n<p>The 90s Foodie</p>")
    state["index"] = (idx + 1) % len(BANK)
    botlib.save_state("snackoclock.json", state)
    print(f"Snack o'clock done: {snack} ({idx + 1}/{len(BANK)})")


if __name__ == "__main__":
    main()
