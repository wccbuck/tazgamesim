import random
import copy
import state, futureState
from init import *
from classes import *

surpriseCards = initDeck("carddata/surprise.yaml", "surprise")
fkcCards = initDeck("carddata/fkc.yaml", "fkc")
challengeDecks = initDeck("carddata/challenge.yaml", "challenge")

initGame("game_setup.yaml", challengeDecks)

# maxNameLength = 0
# cardName = ""
# for deck in challengeDecks:
#     for card in deck["cards"]:
#         if len(card.name) > maxNameLength:
#             maxNameLength = len(card.name)
#             cardName = card.name
#         if len(card.reverse.name) > maxNameLength:
#             maxNameLength = len(card.reverse.name)
#             cardName = card.reverse.name
# print(f"Max card name length: {maxNameLength}")
# print(f"({cardName})")

####
# state.challengeDiscard.append(state.villainDeck.pop(0))


def displayGameState():

    activeCards = [state.villainDeck[0], state.relicDeck[0], state.locationDeck[0]]
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
        f"|\____|            |____/||\____|            |____/||\____|            |____/|"
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
        f"|        {cardStrings[2].storyBonus}        |"
        f"|        {cardStrings[1].storyBonus}        |"
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
        f"\nOngoing +{state.surprise.ongoingBonus} bonus against {state.surprise.ongoingBonusVS}"
        if activeSurpriseCard
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
        print(f"  {prefix}{player.classname}{suffix}")
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


for _ in range(6):

    displayGameState()
    activeCards = [state.villainDeck[0], state.relicDeck[0], state.locationDeck[0]]

    pc = state.players[state.currentPlayer]
    pcClass = pc.classname

    print(f"\nThe {pcClass}'s potential strength against each challenge:")
    for card in activeCards:
        print(
            f"  {card.name}: {pc.totalStrength(card)} vs {card.getDifficulty()} ({getProbPercentile(card, pc)}%)"
            f"\n    Priority: {getPriority(card, pc)}"
        )

    options = []
    for card in activeCards:
        if not card.effect == "spend action token to engage" or pc.hasToken:
            # consider the option of getting tokens back from Binicorn or Ring of Recall
            options.append(Option(card.name, card, pc))

    options = sorted(options, reverse=True)

    print(
        f"\n\nTaking action on \033[1m{options[0].name}\033[0m. Press enter to continue..."
    )
    input()
    options[0].takeAction()
    displayHealth()
    print("Press enter to continue to the next player's turn.")
    # print("Btw, current player's loot cards:")
    # print(pc.lootCards)
    input()
####


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
