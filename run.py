import random
import copy
import statistics
import state, futureState
from time import sleep
from init import *
from classes import *

initGame("game_setup.yaml")

####
# state.challengeDiscard.append(state.villainDeck.pop(0))
# turnsRemaining = len(state.players) - 1 - state.currentPlayer
# assistOpportunities = getNumberOfAssistOpportunities(turnsRemaining)
# assistTokensAvailable = len([True for player in state.players if player.hasToken])
# assistTokensExpended = len(state.players) - assistTokensAvailable
# print(min(max(assistOpportunities - assistTokensAvailable, 0), assistTokensExpended))
#
# print(assistOpportunities, assistTokensAvailable, assistTokensExpended)
####
# state.health = 7
# state.villainDeck.insert(0, state.surpriseDeck.pop())
# state.villainDeck[0].currentDeck = "villain"
# state.villainDeck[0].reveal()
# print(state.surprise.name, state.surprise.discardEffect)
# state.relicDeck.insert(0, state.surpriseDeck.pop())
# state.relicDeck[0].currentDeck = "relic"
# state.relicDeck[0].reveal()
# print(state.surprise.name, state.surprise.discardEffect)
####
####
# Check for typos in challenge.yaml
####
# challengeDecks = []
# with open("carddata/challenge.yaml", "r") as file:
#     try:
#         challengeDecks = yaml.safe_load(file)
#     except yaml.YAMLError as exc:
#         print(exc)
# keys, icons = getUniqueChallengeDeckKeysAndIcons(challengeDecks)
# keys.sort()
# icons.sort()
# print("Keys:")
# for key in keys:
#     print("\t" + key)
# print("Icons:")
# for icon in icons:
#     print("\t" + icon)
####


def displayGameState():

    activeCards = getActiveCards()
    cardStrings = []
    headers = [
        f"Villain: {state.villain}",
        f"Relic: {state.relic}",
        f"Location: {state.location}",
    ]

    for i in range(3):
        headers[i] = f"{headers[i]:^26}"

    for card in activeCards:
        cs = type("", (), {})()
        cs.name = f"{card.name:^24}"

        cs.difficulty = str(card.difficulty)
        if len(cs.difficulty) < 2:
            cs.difficulty = " " + cs.difficulty
        cs.leftDiff = str(card.leftDiff) if card.leftDiff != 0 else "  "
        if card.leftDiff > 0:
            cs.leftDiff = "+" + cs.leftDiff
        cs.rightDiff = str(card.rightDiff) if card.rightDiff != 0 else "  "
        if card.rightDiff > 0:
            cs.rightDiff = "+" + cs.rightDiff
        cs.diffMod = str(card.diffMod) if card.diffMod != 0 else "   "
        if card.diffMod > 0:
            cs.diffMod = "+" + cs.diffMod
        if len(cs.diffMod) < 3:
            cs.diffMod = cs.diffMod + " "

        cs.loot = str(card.loot)
        if len(cs.loot) < 2:
            cs.loot = " " + cs.loot
        cs.damage = str(card.getDamage())
        if len(cs.damage) < 2:
            cs.damage = " " + cs.damage

        cs.icons1 = ""
        cs.icons2 = ""
        for icon in card.icons:
            if icon == card.icons[-1]:  # last
                if len(cs.icons1 + icon) <= 21:
                    cs.icons1 = cs.icons1 + icon
                else:
                    cs.icons2 = cs.icons2 + icon
            else:
                if len(cs.icons1 + icon + ", ") <= 22:
                    cs.icons1 = cs.icons1 + icon + ", "
                else:
                    cs.icons2 = cs.icons2 + icon + ", "

        cs.icons1 = f"{cs.icons1:^22}"
        cs.icons2 = f"{cs.icons2:^22}"

        cs.storyBonus = "Story +1" if card.storyBonus else "        "

        cs.effect1 = ""
        cs.effect2 = ""
        effectWords = card.effect.split(" ") if card.effect else []
        for word in effectWords:
            if word == effectWords[-1]:  # last
                if len(cs.effect1 + word) <= 21:
                    cs.effect1 = cs.effect1 + word
                else:
                    cs.effect2 = cs.effect2 + word
            else:
                if len(cs.effect1 + word + " ") <= 22:
                    cs.effect1 = cs.effect1 + word + " "
                else:
                    cs.effect2 = cs.effect2 + word + " "
        cs.effect1 = f"{cs.effect1:^22}"
        cs.effect2 = f"{cs.effect2:^22}"

        cs.fail1 = "fail: " if card.failEffect else ""
        cs.fail2 = ""
        failWords = card.failEffect.split(" ") if card.failEffect else []
        for word in failWords:
            if word == failWords[-1]:  # last
                if len(cs.fail1 + word) <= 21:
                    cs.fail1 = cs.fail1 + word
                else:
                    cs.fail2 = cs.fail2 + word
            else:
                if len(cs.fail1 + word + " ") <= 22:
                    cs.fail1 = cs.fail1 + word + " "
                else:
                    cs.fail2 = cs.fail2 + word + " "
        cs.fail1 = f"{cs.fail1:^22}"
        cs.fail2 = f"{cs.fail2:^22}"

        cs.succeed1 = "succeed: " if card.succeedEffect else ""
        cs.succeed2 = ""
        succeedWords = card.succeedEffect.split(" ") if card.succeedEffect else []
        for word in succeedWords:
            if word == succeedWords[-1]:  # last
                if len(cs.succeed1 + word) <= 21:
                    cs.succeed1 = cs.succeed1 + word
                else:
                    cs.succeed2 = cs.succeed2 + word
            else:
                if len(cs.succeed1 + word + " ") <= 22:
                    cs.succeed1 = cs.succeed1 + word + " "
                else:
                    cs.succeed2 = cs.succeed2 + word + " "
        cs.succeed1 = f"{cs.succeed1:^22}"
        cs.succeed2 = f"{cs.succeed2:^22}"

        cs.deck = f"{card.deck:^11}"

        cs.number = f"    {card.number} " if card.number != 0 else "      "
        if card.finale:
            cs.number = "FINALE"

        cardStrings.append(cs)

    print("\n                           \033[1mActive Challenge Cards:\033[0m\n")
    print(f"{headers[0]}{headers[1]}{headers[2]}")
    print(
        f" ________________________  ________________________  ________________________ "
    )
    print(
        f"/|    |            |    |\\/|    |            |    |\\/|    |            |    |\\"
    )
    print(
        f"|| {cardStrings[0].leftDiff} |     {cardStrings[0].difficulty}     | {cardStrings[0].rightDiff} ||"
        f"|| {cardStrings[1].leftDiff} |     {cardStrings[1].difficulty}     | {cardStrings[1].rightDiff} ||"
        f"|| {cardStrings[2].leftDiff} |     {cardStrings[2].difficulty}     | {cardStrings[2].rightDiff} ||"
    )
    print(
        f"|\____|     {cardStrings[0].diffMod}    |____/|"
        f"|\____|     {cardStrings[1].diffMod}    |____/|"
        f"|\____|     {cardStrings[2].diffMod}    |____/|"
    )
    print(
        f"|      \__________/      ||      \__________/      ||      \__________/      |"
    )
    print(
        f"|                        ||                        ||                        |"
    )
    print(f"|{cardStrings[0].name}||{cardStrings[1].name}||{cardStrings[2].name}|")
    print(
        f"|                        ||                        ||                        |"
    )
    print(
        f"| {cardStrings[0].icons1} || {cardStrings[1].icons1} || {cardStrings[2].icons1} |"
    )
    print(
        f"| {cardStrings[0].icons2} || {cardStrings[1].icons2} || {cardStrings[2].icons2} |"
    )
    print(
        f"|                        ||                        ||                        |"
    )
    print(
        f"|        {cardStrings[0].storyBonus}        |"
        f"|        {cardStrings[1].storyBonus}        |"
        f"|        {cardStrings[2].storyBonus}        |"
    )
    print(
        f"| {cardStrings[0].effect1} || {cardStrings[1].effect1} || {cardStrings[2].effect1} |"
    )
    print(
        f"| {cardStrings[0].effect2} || {cardStrings[1].effect2} || {cardStrings[2].effect2} |"
    )
    print(
        f"| {cardStrings[0].fail1} || {cardStrings[1].fail1} || {cardStrings[2].fail1} |"
    )
    print(
        f"| {cardStrings[0].fail2} || {cardStrings[1].fail2} || {cardStrings[2].fail2} |"
    )
    print(
        f"| {cardStrings[0].succeed1} || {cardStrings[1].succeed1} || {cardStrings[2].succeed1} |"
    )
    print(
        f"| {cardStrings[0].succeed2} || {cardStrings[1].succeed2} || {cardStrings[2].succeed2} |"
    )
    print(
        f"|                        ||                        ||                        |"
    )
    print(
        f"| loot  {cardStrings[0].deck}  dmg |"
        f"| loot  {cardStrings[1].deck}  dmg |"
        f"| loot  {cardStrings[2].deck}  dmg |"
    )
    print(
        f"| {cardStrings[0].loot}     {cardStrings[0].number}      {cardStrings[0].damage}  |"
        f"| {cardStrings[1].loot}     {cardStrings[1].number}      {cardStrings[1].damage}  |"
        f"| {cardStrings[2].loot}     {cardStrings[2].number}      {cardStrings[2].damage}  |"
    )
    print(
        f"\________________________/\________________________/\________________________/"
    )
    print(
        "=============================================================================="
    )
    print("\n\033[1mSurprise Card:\033[0m ")
    activeSurpriseCard = state.surprise is not None
    surpriseCardName = state.surprise.name if activeSurpriseCard else "(None)"
    surpriseCardIcons = (
        ", ".join(state.surprise.ongoingBonusVS) if activeSurpriseCard else ""
    )
    surpriseCardOngoingBonus = (
        f"\nOngoing +{state.surprise.ongoingBonus} bonus against {surpriseCardIcons}"
        if activeSurpriseCard and state.surprise.ongoingBonusVS
        else ""
    )
    surpriseCardDiscardEffect = (
        f"\nDiscard Effect: {state.surprise.discardEffect}"
        if activeSurpriseCard
        else ""
    )
    print(f"{surpriseCardName}{surpriseCardOngoingBonus}{surpriseCardDiscardEffect}\n")
    print(
        "=============================================================================="
    )
    print()
    displayHealth()

    print(f"\n\033[1mPlayers: \033[0m")
    for player in state.players:
        prefix = (
            "\033[92;1m" if player == state.players[state.currentPlayer] else "\033[1m"
        )
        suffix = "\033[0m"
        print(f"  {prefix}{player.name}{suffix}")
        print(f"    has token: {player.hasToken}")
        fkcCards = ", ".join(card.name for card in player.fkcCards)
        lootCards = ", ".join(f"{card.name} ({card.loot})" for card in player.lootCards)
        print(f"    fkc cards: {fkcCards}")
        print(f"    loot: {lootCards}")

    print(
        "=============================================================================="
    )


def displayHealth():
    prefix = "\033[93m"
    if state.health == state.maxHealth:
        prefix = "\033[94m"
    if state.health < 4:
        prefix = "\033[91m"
    print(f"\033[1mCurrent Health:{prefix} {state.health}\033[0m")


####
# Testing adding loot cards
####
# while True:
#     displayGameState()
#     activeCards = getActiveCards()
#     pc = state.players[state.currentPlayer]
#     fkcCards = ", ".join(card.name for card in pc.fkcCards)
#     lootCards = ", ".join(f"{card.name} ({card.loot})" for card in pc.lootCards)
#     print(f"{pc.name}'s loot cards:")
#     print(lootCards)
#     print(f"{pc.name}'s fkc cards:")
#     print(fkcCards)
#     index = random.choice(range(1, 3))
#     print(f"Adding {activeCards[index].name} (loot {activeCards[index].loot}).")
#     input()
#     lootCard = getDeckFromType(activeCards[index].currentDeck).pop(0)
#     pc.addLootCard(lootCard)
####
# Testing post-roll potential helpers
####
# minimumNeeded = 4
# potentialHelpers = [
#     {"name": "wow", "assist": 1, "pc": True, "holdPriority": 0},
#     {"name": "yep", "assist": 1, "pc": False, "holdPriority": 1},
#     {"name": "bob", "assist": 4, "pc": True, "holdPriority": 1.6},
#     {"name": "foo", "assist": 2, "pc": False, "holdPriority": 1},
#     {"name": "bar", "assist": 1, "pc": True, "holdPriority": 0.5},
# ]
# maxAssists = 1
#
#
# def makeSetsOfUsefulHelpers(setsOfUsefulHelpers, potentialHelpers, newSet):
#     for index, potentialHelper in enumerate(potentialHelpers):
#         newSet.append(potentialHelper)
#         if len([helper for helper in newSet if helper["pc"]]) <= maxAssists:
#             helpSum = sum([helper["assist"] for helper in newSet])
#             if helpSum >= minimumNeeded:
#                 setsOfUsefulHelpers.append(newSet.copy())
#             else:
#                 makeSetsOfUsefulHelpers(
#                     setsOfUsefulHelpers, potentialHelpers[index + 1 :], newSet
#                 )
#         helper = newSet.pop()
#
#
# setsOfUsefulHelpers = []
# makeSetsOfUsefulHelpers(setsOfUsefulHelpers, potentialHelpers, [])
# setsOfUsefulHelpers = sorted(
#     setsOfUsefulHelpers, key=lambda set: sum([x["holdPriority"] for x in set])
# )
# for set in setsOfUsefulHelpers:
#     print(str([f"{helper['name']} ({helper['holdPriority']})" for helper in set]))
####
# Main Game Loop
####
# for fkcCard in state.fkcDeck:
#     if fkcCard.name == "The Flaming Raging Poisoning Sword of Doom":
#         getPlayerCharacter("bard").addFkcCard(fkcCard)
#         break
if state.display:
    for _ in range(state.runs):
        while True:
            displayGameState()
            activeCards = getActiveCards()

            pc = state.players[state.currentPlayer]
            pcClass = pc.name

            options = assembleOptions()
            helper = (
                ", ".join(helper.name for helper in options[0].helpers)
                if options[0].helpers
                else "(none)"
            )
            # testing
            for option in options:
                print(
                    f"\t* {option.name} with helpers {str([helper.name for helper in option.helpers])}: priority {option.priority:.2f}, success {option.success:.2f}, failure {option.failure:.2f}"
                )
            print(
                f"\n\nTaking action on \033[1m{options[0].name}\033[0m, helper = {helper}. Press enter to continue..."
            )
            if not state.skipPauses:
                input()
            options[0].takeAction()

            displayHealth()
            if state.won is not None:
                if state.won:
                    print("Win!")
                    break
                else:
                    print("Loss!")
                    break
            print("Press enter to continue to the next player's turn.")
            # print("Btw, current player's loot cards:")
            # print(pc.lootCards)
            if not state.skipPauses:
                input()
        reinitGame("game_setup.yaml")
        print("Next Game...")
        input()
        # for _ in range(20):
        #     print(
        #         "################################################################################################################"
        #     )
        # sleep(1)
else:
    results = []

    for i in range(state.runs):
        result = {}
        result["turnCount"] = 0
        while True:
            result["turnCount"] += 1
            activeCards = getActiveCards()
            options = assembleOptions()

            options[0].takeAction()

            if state.won is not None:
                if state.won:
                    result["won"] = True
                    result["health"] = state.health
                    results.append(result)
                    break
                else:
                    result["won"] = False
                    result["health"] = state.health
                    results.append(result)
                    break
        if (i + 1) % 10 == 0:
            winrate = (
                100.0
                * len([result for result in results if result["won"]])
                / len(results)
            )
            print(f"{i + 1} ({winrate:.2f}% winrate)")

        reinitGame("game_setup.yaml")

    wins = len([result for result in results if result["won"]])
    losses = len([result for result in results if not result["won"]])
    turnCount = statistics.mean([result["turnCount"] for result in results])
    tcStdev = statistics.stdev([result["turnCount"] for result in results])
    print(f"Wins: {wins}, Losses: {losses}")
    print(f"Average turn count: {turnCount:.2f} ± {tcStdev:.2f}")
    # print(state.priorities["clear 1 card a"])


#####

# state.surprise = random.choice(surpriseCards)
# print("surprise card: " + state.surprise.name)
#
#
# print(pc.totalStrength(challengeCard))

#####

# print(len(fkcCards))
#
# fkcCard = random.choice(fkcCards)
# print(fkcCard.name)


# for fkcCard in fkcCards:
#     if fkcCard.name == "Scoundrel's Dice":
#         fkcCards.remove(fkcCard)
#         pc.addFkcCard(fkcCard)
#         break
# print(pc.totalStrength(challengeCard))
#
# for fkcCard in fkcCards:
#     if fkcCard.name == "Ring of Greed":
#         fkcCards.remove(fkcCard)
#         pc.addFkcCard(fkcCard)
#         break
# print(pc.totalStrength(challengeCard))

####

# for _ in range(4):
#     random.shuffle(fkcCards)
#     newFkcCard = fkcCards.pop()
#     pc.addFkcCard(newFkcCard)
#     for card in pc.fkcCards:
#         print(card.name)
#     print("---")

#
# sc1 = SurpriseCard(
#     name="G'Nash Lends A Hand",
#     ongoingBonusVS="monster",
#     discardEffect="no damage after fail",
# )
