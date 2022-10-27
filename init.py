import yaml
import copy
import os, sys
import state, futureState

from classes import *


def initDeck(url, type):
    cards = []

    cardDicts = []

    with open(url, "r") as file:
        try:
            cardDicts = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

    for cd in cardDicts:
        if type == "surprise":
            cards.append(SurpriseCard(**cd))
        if type == "fkc":
            cards.append(FKCCard(**cd))
        if type == "challenge":
            challengeCards = []
            deck = cd["deck"]
            decktype = cd["decktype"]
            for card in cd["cards"]:
                frontCard = ChallengeCard(deck=deck, decktype=decktype, **card["front"])
                backCard = ChallengeCard(deck=deck, decktype=decktype, **card["back"])
                frontCard.reverse = backCard
                backCard.reverse = frontCard
                challengeCards.append(frontCard)

            # shuffle, arrange
            for index, card in enumerate(challengeCards):
                if not card.finale and random.randint(0, 1) == 1:
                    challengeCards[index] = card.reverse
            if deck in ["idol", "cult"]:
                for index, card in enumerate(challengeCards):
                    if card.number == 2:
                        challengeCards[index] = card.reverse
            if deck in ["staff", "idol", "cult", "ring", "sword", "sash", "hoard"]:
                finaleCard = challengeCards.pop()
                random.shuffle(challengeCards)
                challengeCards.append(finaleCard)
            cards.append({"name": deck, "cards": challengeCards})

    return cards


def getChallengeDeck(deckName, challengeDecks):
    challengeDeck = []
    for deck in challengeDecks:
        if deck["name"] == deckName:
            challengeDeck = deck["cards"]
    return challengeDeck


def getUniqueChallengeDeckKeysAndIcons(challengeDecks):
    keys = []
    icons = []
    for deck in challengeDecks:
        for card in deck["cards"]:
            for key in card["front"].keys():
                if key not in keys:
                    keys.append(key)
            if "icons" in card["front"].keys():
                for icon in card["front"]["icons"]:
                    if icon not in icons:
                        icons.append(icon)
            for key in card["back"].keys():
                if key not in keys:
                    keys.append(key)
            if "icons" in card["back"].keys():
                for icon in card["back"]["icons"]:
                    if icon not in icons:
                        icons.append(icon)
    return keys, icons


def initGame(url):

    state.won = None
    state.surpriseDeck = initDeck("carddata/surprise.yaml", "surprise")
    random.shuffle(state.surpriseDeck)
    state.fkcDeck = initDeck("carddata/fkc.yaml", "fkc")
    random.shuffle(state.fkcDeck)
    challengeDecks = initDeck("carddata/challenge.yaml", "challenge")

    with open("priorities.yaml", "r") as file:
        try:
            state.priorities = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

    gameSetupDict = {}
    with open(url, "r") as file:
        try:
            gameSetupDict = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)
    state.skipPauses = (
        "skipPauses" in gameSetupDict and gameSetupDict["skipPauses"] == True
    )
    state.display = gameSetupDict["display"] == True
    state.runs = gameSetupDict["runs"] or 1
    state.villain = gameSetupDict["villain"]
    state.relic = gameSetupDict["relic"]
    state.location = gameSetupDict["location"]
    state.villainDeck = getChallengeDeck(state.villain, challengeDecks)
    state.relicDeck = getChallengeDeck(state.relic, challengeDecks)
    state.locationDeck = getChallengeDeck(state.location, challengeDecks)

    sc1 = state.surpriseDeck.pop()
    sc1.currentDeck = "villain"
    state.villainDeck.insert(4, sc1)
    sc2 = state.surpriseDeck.pop()
    sc2.currentDeck = "relic"
    state.relicDeck.insert(4, sc2)
    sc3 = state.surpriseDeck.pop()
    sc3.currentDeck = "location"
    state.locationDeck.insert(4, sc3)

    state.players = [PlayerCharacter(name) for name in gameSetupDict["players"]]
    random.shuffle(state.players)
    state.currentPlayer = 0

    numPlayers = len(state.players)
    state.maxHealth = {
        3: 12,
        4: 10,
        5: 10,
    }.get(numPlayers, 10)
    state.health = state.maxHealth

    for card in [state.villainDeck[0], state.relicDeck[0], state.locationDeck[0]]:
        card.reveal()

    state.trainRaceTokenHouseRule = (
        "trainRaceTokenHouseRule" in gameSetupDict
        and gameSetupDict["trainRaceTokenHouseRule"] == True
    )


def reinitGame(url):

    state.challengeDiscard = []
    state.surpriseDiscard = []
    state.fkcDiscard = []
    state.surprise = None
    state.health = state.maxHealth
    state.currentPlayer = 0
    state.relicTokens = 0
    state.pendingDamage = 0
    state.relicCounters = 0
    state.won = None
    state.surpriseDeck = initDeck("carddata/surprise.yaml", "surprise")
    random.shuffle(state.surpriseDeck)
    state.fkcDeck = initDeck("carddata/fkc.yaml", "fkc")
    random.shuffle(state.fkcDeck)
    challengeDecks = initDeck("carddata/challenge.yaml", "challenge")

    gameSetupDict = {}
    with open(url, "r") as file:
        try:
            gameSetupDict = yaml.safe_load(file)
        except yaml.YAMLError as exc:
            print(exc)

    state.villainDeck = getChallengeDeck(state.villain, challengeDecks)
    state.relicDeck = getChallengeDeck(state.relic, challengeDecks)
    state.locationDeck = getChallengeDeck(state.location, challengeDecks)

    sc1 = state.surpriseDeck.pop()
    sc1.currentDeck = "villain"
    state.villainDeck.insert(4, sc1)
    sc2 = state.surpriseDeck.pop()
    sc2.currentDeck = "relic"
    state.relicDeck.insert(4, sc2)
    sc3 = state.surpriseDeck.pop()
    sc3.currentDeck = "location"
    state.locationDeck.insert(4, sc3)

    for card in [state.villainDeck[0], state.relicDeck[0], state.locationDeck[0]]:
        card.reveal()

    state.players = [PlayerCharacter(name) for name in gameSetupDict["players"]]
    random.shuffle(state.players)
    state.currentPlayer = 0
