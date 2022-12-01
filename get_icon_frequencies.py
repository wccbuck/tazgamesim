from init import *
from classes import *

readGameSetup("game_setup.yaml")
initGame()

challengeDecks = []
with open("carddata/challenge.yaml", "r") as file:
    try:
        challengeDecks = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)
results = []
for deck in challengeDecks:
    newResult = {
        "deck": deck["deck"],
        "monster": 0,
        "trap": 0,
        "magic": 0,
        "spooky": 0,
        "no type": 0,
        "double assist": 0,
        "no assist": 0,
        "chance": 0,
        "no dice": 0
    }
    for card in deck["cards"]:
        for side in ["front", "back"]:
            if "icons" in card[side]:
                foundType = False
                for icon in card[side]["icons"]:
                    if icon in ["monster", "trap", "magic", "spooky"]:
                        foundType = True
                    newResult[icon] += 1
                if not foundType:
                    newResult["no type"] += 1
            else:
                newResult["no type"] += 1
    results.append(newResult)

for result in results:
    print(f"{result['deck']}\t{result['monster']}\t{result['trap']}\t{result['magic']}\t{result['spooky']}\t{result['no type']}\t{result['double assist']}\t{result['no assist']}\t{result['chance']}\t{result['no dice']}")
