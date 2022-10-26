from init import *
from classes import *

initGame("game_setup.yaml")

####
# Get "average" villain/relic/location card
# useful for generic stand-in challenge cards for lookAhead
####
decktype = "relic"
challengeDecks = []
with open("carddata/challenge.yaml", "r") as file:
    try:
        challengeDecks = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)

count = 0
difficulty = 0
loot = 0
damage = 0
for deck in challengeDecks:
    if deck["decktype"] == decktype:
        for card in deck["cards"]:
            if not "finale" in card["front"].keys():
                for side in ["front", "back"]:
                    count += 1
                    difficulty += card[side]["difficulty"]
                    if "storyBonus" in card[side].keys():
                        difficulty -= card[side]["storyBonus"]
                    if (
                        "chance" in card[side].keys()
                        and "chance" in card[side]["icons"]
                    ) or (
                        "no dice" in card[side].keys()
                        and "no dice" in card[side]["icons"]
                    ):
                        difficulty += 3.5
                    if "loot" in card[side].keys():
                        loot += card[side]["loot"]
                    else:
                        loot += 1
                    if "damage" in card[side].keys():
                        damage += card[side]["damage"]
                    else:
                        damage += 1
print(decktype)
print(f"Difficulty: {difficulty/count}")
print(f"Loot: {loot/count}")
print(f"Damage: {damage/count}")
