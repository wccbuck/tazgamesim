import yaml
import copy
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
            if deck in ["staff", "idol", "cult"]:
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


def initGame(url, challengeDecks):
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
    state.villain = gameSetupDict["villain"]
    state.relic = gameSetupDict["relic"]
    state.location = gameSetupDict["location"]
    state.villainDeck = getChallengeDeck(state.villain, challengeDecks)
    state.relicDeck = getChallengeDeck(state.relic, challengeDecks)
    state.locationDeck = getChallengeDeck(state.location, challengeDecks)

    state.players = [
        PlayerCharacter(classname) for classname in gameSetupDict["players"]
    ]
    state.currentPlayer = 0

    copyState()
