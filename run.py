import random
import copy
import statistics
import math
import os
import state, futureState
from time import sleep
from init import *
from classes import *

if os.name != "nt":
    import fcntl


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
        if cs.effect1.strip() == "":
            if card.defeatCounters > 0:
                cs.effect1 = f"defeatCounters: {card.currentDefeatCounters}"
                cs.effect1 = f"{cs.effect1:^22}"

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
        if cs.fail1.strip() == "":
            cs.fail1 = "failAny: " if card.failAnyEffect else ""
            cs.fail2 = ""
            failWords = card.failAnyEffect.split(" ") if card.failAnyEffect else []
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
# Main Game Loop
####

readGameSetup("game_setup.yaml")

if state.display:
    # only runs first villain/relic/location in list
    for _ in range(state.runs):
        while True:
            displayGameState()
            activeCards = getActiveCards()

            pc = state.players[state.currentPlayer]
            pcClass = pc.name

            options = assembleOptions()
            helper = (
                ", ".join(
                    (
                        f"{helper.name} ({helper.quantity})"
                        if hasattr(helper, "quantity")
                        else helper.name
                    )
                    for helper in options[0].helpers
                )
                if options[0].helpers
                else "(none)"
            )
            # testing
            for option in options:
                optionhelpers = str(
                    [
                        (
                            f"{helper.name} ({helper.quantity})"
                            if hasattr(helper, "quantity")
                            else helper.name
                        )
                        for helper in option.helpers
                    ]
                )
                print(
                    f"\t* {option.name} with helpers {optionhelpers}: priority {option.priority:.2f}, success {option.success:.2f}, failure {option.failure:.2f}"
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

        reinitGame()
        print("Next Game...")
        input()
        # for _ in range(20):
        #     print(
        #         "################################################################################################################"
        #     )
        # sleep(1)
else:
    for vIndex in range(len(state.gameSetupDict["villain"])):
        for rIndex in range(len(state.gameSetupDict["relic"])):
            for lIndex in range(len(state.gameSetupDict["location"])):
                initGame(vIndex, rIndex, lIndex)
                players = ", ".join(pc for pc in state.gameSetupDict["players"])
                print(
                    f"Beginning {state.runs} simulated games on ({state.villain}, {state.relic}, {state.location}) with players ({players})"
                )
                results = []

                for i in range(state.runs):
                    try:
                        result = {}
                        result["turnCount"] = 0
                        result["nemesisShowedUpFirstFiveCards"] = False
                        if state.relic == "hoard":
                            for index in range(
                                7
                            ):  # cards 0-6, since card 4 is a surprise card
                                if state.relicDeck[index].name == "Your Nemesis":
                                    result["nemesisShowedUpFirstFiveCards"] = True
                                    break
                        while True:
                            result["turnCount"] += 1
                            options = assembleOptions()

                            options[0].takeAction()

                            if state.won is not None:
                                if state.won:
                                    result["won"] = True
                                    result["clearedVillain"] = deckDefeated("villain")
                                    result["clearedLocation"] = deckDefeated("location")
                                else:
                                    result["won"] = False
                                    if state.location in ["train", "race"]:
                                        # did we reach the end of the line
                                        result["trainRaceEOL"] = state.locationDeck[
                                            0
                                        ].finale

                                result["health"] = state.health
                                results.append(result)
                                break
                        if (i + 1) % 10 == 0:
                            winratePct = (
                                100.0
                                * len([result for result in results if result["won"]])
                                / len(results)
                            )
                            print(f"{i + 1} ({winratePct:.2f}% winrate)")

                        reinitGame()
                    except KeyboardInterrupt:
                        print(" >> keyboard interrupt")
                        break

                wins = len([result for result in results if result["won"]])
                losses = len([result for result in results if not result["won"]])
                winrate = wins / len(results)
                winratePct = 100.0 * wins / len(results)
                wrError = 100.0 * (
                    1.96 * math.sqrt((winrate * (1 - winrate)) / (i + 1))
                )
                wrLowerBound = winratePct - wrError
                wrUpperBound = winratePct + wrError
                turnCount = statistics.mean([result["turnCount"] for result in results])
                tcStdev = statistics.stdev([result["turnCount"] for result in results])
                winHealth = statistics.mean(
                    [result["health"] for result in results if result["won"]]
                )
                villainWins = len(
                    [
                        result
                        for result in results
                        if result["won"] and result["clearedVillain"]
                    ]
                )
                locationWins = len(
                    [
                        result
                        for result in results
                        if result["won"] and result["clearedLocation"]
                    ]
                )
                completeWins = len(
                    [
                        result
                        for result in results
                        if result["won"]
                        and result["clearedVillain"]
                        and result["clearedLocation"]
                    ]
                )
                villainWinsPct = 100.0 * villainWins / wins
                locationWinsPct = 100.0 * locationWins / wins
                completeWinsPct = 100.0 * completeWins / wins
                print("#####################")
                print(f"Win rate: {winratePct:.2f}%")
                print(f"Wins: {wins}, Losses: {losses} (Total: {wins+losses})")
                print(f"Average turn count: {turnCount:.2f} ± {tcStdev:.2f}")
                print(
                    f"Percentage of wins where villain was defeated: {villainWinsPct:.2f}%"
                )
                print(
                    f"Percentage of wins where location was cleared: {locationWinsPct:.2f}%"
                )
                print(
                    f"Percentage of wins where both villain and location were cleared: {completeWinsPct:.2f}%"
                )
                eolLossesPct = 0
                avgEOLHealth = 0
                wrNemesisShowedUp = 0
                wrNoNemesisShowedUp = 0
                if state.location in ["train", "race"]:
                    eolLosses = len(
                        [
                            result
                            for result in results
                            if not result["won"] and result["trainRaceEOL"]
                        ]
                    )
                    eolLossesPct = 100.0 * eolLosses / losses
                    avgEOLHealth = statistics.mean(
                        [
                            result["health"]
                            for result in results
                            if not result["won"] and result["trainRaceEOL"]
                        ]
                    )
                    print(
                        f"Percentage of losses where we reached the end of the location deck: {eolLossesPct:.2f}%"
                    )
                    print(
                        f"Average remaining health in those games: {avgEOLHealth:.2f}"
                    )
                if state.relic == "hoard":
                    nemesisWins = len(
                        [
                            result
                            for result in results
                            if result["nemesisShowedUpFirstFiveCards"] and result["won"]
                        ]
                    )
                    nemesisCount = len(
                        [
                            result
                            for result in results
                            if result["nemesisShowedUpFirstFiveCards"]
                        ]
                    )
                    noNemesisWins = len(
                        [
                            result
                            for result in results
                            if not result["nemesisShowedUpFirstFiveCards"]
                            and result["won"]
                        ]
                    )
                    noNemesisCount = len(
                        [
                            result
                            for result in results
                            if not result["nemesisShowedUpFirstFiveCards"]
                        ]
                    )
                    if nemesisCount > 0 and noNemesisCount > 0:
                        wrNemesisShowedUp = 100.0 * nemesisWins / nemesisCount
                        wrNoNemesisShowedUp = 100.0 * noNemesisWins / noNemesisCount
                        print(
                            f"Win Rate where 'Your Nemesis' showed up within the first five challenge cards of the relic deck: {wrNemesisShowedUp}%"
                        )
                        print(f"Win Rate otherwise: {wrNoNemesisShowedUp}%")

                gameKey = f"{state.villain}-{state.relic}-{state.location}-"
                playerList = [player.name for player in state.players]
                playerList.sort()
                playerListString = "-".join(playerList)
                gameKey += playerListString
                gameKey = gameKey.replace(" ", "")
                print("\nKey for this game:")
                print(gameKey)
                print(
                    "winratePct\twrLowerBound\twrUpperBound\tturnCount\ttcStdev\twinHealth\tvillainWinsPct\tlocationWinsPct\tcompleteWinsPct\teolLossesPct\tavgEOLHealth\twrNemesisShowedUp\twrNoNemesisShowedUp"
                )
                print(
                    f"{winratePct}\t{wrLowerBound}\t{wrUpperBound}\t{turnCount}\t{tcStdev}\t{winHealth}\t{villainWinsPct}\t{locationWinsPct}\t{completeWinsPct}\t{eolLossesPct}\t{avgEOLHealth}\t{wrNemesisShowedUp}\t{wrNoNemesisShowedUp}"
                )
                resultsFilename = state.gameSetupDict["resultsFilename"]
                print(f"\nRecording results in {resultsFilename}.\n")
                print("#####################")
                with open(resultsFilename, "a") as file:
                    if os.name != "nt":
                        fcntl.flock(file, fcntl.LOCK_EX)
                    file.write(gameKey)
                    file.write(f"\nCompleted Runs: {(i + 1)}")
                    file.write(
                        f"\n{winratePct}\t{wrLowerBound}\t{wrUpperBound}\t{turnCount}\t{tcStdev}\t{winHealth}\t{villainWinsPct}\t{locationWinsPct}\t{completeWinsPct}\t{eolLossesPct}\t{avgEOLHealth}\t{wrNemesisShowedUp}\t{wrNoNemesisShowedUp}\n\n"
                    )
                    if os.name != "nt":
                        file.flush()
                        fcntl.flock(file, fcntl.LOCK_UN)
