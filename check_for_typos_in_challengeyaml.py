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
keys, icons = getUniqueChallengeDeckKeysAndIcons(challengeDecks)
keys.sort()
icons.sort()
print("Keys:")
for key in keys:
    print("\t" + key)
print("Icons:")
for icon in icons:
    print("\t" + icon)
