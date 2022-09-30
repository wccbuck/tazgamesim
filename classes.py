import random
import copy
import state, futureState


###########
# Classes #
###########


class PlayerCharacter:
    def __init__(self, classname):
        if classname.lower() not in ["warrior", "rogue", "priest", "bard", "wizard"]:
            raise ValueError(f"Invalid class name: {classname}")
        self.classname = classname.lower()
        self.lootCards = []
        self.fkcCards = []
        self.hasToken = True

    def baseStrength(self, ChallengeCard):
        returnval = 4

        if "baseStrength always 4" in [
            fkcCard.ongoingEffect for fkcCard in self.fkcCards
        ]:
            return 4

        if self.classname == "warrior" and "monster" not in ChallengeCard.icons:
            returnval = 2
        if self.classname == "rogue" and "trap" not in ChallengeCard.icons:
            returnval = 2
        if self.classname == "priest" and "spooky" not in ChallengeCard.icons:
            returnval = 2
        if self.classname == "wizard" and "magic" not in ChallengeCard.icons:
            returnval = 1
        if self.classname == "bard" and ChallengeCard.decktype != "relic":
            returnval = 1

        return returnval

    def totalStrength(self, challengeCard):
        totalStrength = self.baseStrength(challengeCard)
        totalStrength += challengeCard.storyBonus
        challengeIcons = copy.deepcopy(challengeCard.icons)
        challengeIcons.append("any")
        for fkcCard in self.fkcCards:
            if any(icon in fkcCard.ongoingBonusVS for icon in challengeIcons):
                totalStrength += fkcCard.ongoingBonus
            if (
                "+1 when difficulty greater than 9" == fkcCard.ongoingEffect
                and challengeCard.difficulty > 9
            ):
                totalStrength += 1
        if state.surprise is not None:
            if any(icon in state.surprise.ongoingBonusVS for icon in challengeIcons):
                totalStrength += state.surprise.ongoingBonus
        # more
        return totalStrength

    def addFkcCard(self, newFkcCard):
        # TODO: Add the card, then if we're above the limit,
        # discard or give away lowest-priority card
        # (or the one with the best discard bonus).
        # You just need to get down to 2 by the end of a turn.

        if (
            "no fkc card limit" in [fkcCard.ongoingEffect for fkcCard in self.fkcCards]
            or len(self.fkcCards) < 2
        ):
            self.fkcCards.append(newFkcCard)
        else:
            print("(Can't add new card: " + newFkcCard.name + ")")


class ChallengeCard:
    def __init__(
        self,
        name,
        difficulty,
        deck,
        decktype,
        reverse=None,
        loot=1,
        damage=1,
        leftDiff=0,
        rightDiff=0,
        diffMod=0,
        damageMod=0,
        icons=None,
        effect=None,
        failEffect=None,
        succeedEffect=None,
        number=0,
        storyBonus=0,
        finale=False,
    ):
        self.name = name
        self.baseDifficulty = difficulty
        self.difficulty = difficulty
        self.loot = loot
        self.damage = damage
        self.deck = deck
        self.decktype = decktype  # villain, relic, or location
        self.leftDiff = leftDiff
        self.rightDiff = rightDiff
        self.diffMod = diffMod
        self.damageMod = damageMod
        if icons is None:
            icons = []
        self.icons = icons
        self.effect = effect  # passive effect, not triggered by success or failure
        self.failEffect = failEffect
        self.succeedEffect = succeedEffect
        self.reverse = reverse  # another ChallengeCard object
        self.number = number  # deck order number if relevant, or front/back
        self.storyBonus = storyBonus  # +1 if you add some story
        self.finale = finale
        # currentDeck can change over course of game (e.g. Dark Lord)
        self.currentDeck = decktype

    def reveal(self):
        if "chance" in self.icons:
            self.difficulty = self.baseDifficulty + random.choice(range(1, 7))
        if self.deck == "hoard" and self.effect == "add relic tokens to difficulty":
            self.difficulty = self.difficulty + state.relicTokens

    def getDifficulty(self):
        return (
            self.difficulty
            + self.diffMod
            + cardBoost(self.decktype, "left")
            + cardBoost(self.decktype, "right")
        )

    def getDamage(self):
        return self.damage + self.damageMod


def cardBoost(decktype, leftOrRight):
    if decktype == "villain":
        if leftOrRight == "left":
            return 0
        else:
            return state.relicDeck[0].leftDiff or 0
    if decktype == "relic":
        if leftOrRight == "left":
            return state.villainDeck[0].rightDiff or 0
        else:
            return state.locationDeck[0].leftDiff or 0
    if decktype == "location":
        if leftOrRight == "left":
            return state.relicDeck[0].rightDiff or 0
        else:
            return 0


class SurpriseCard:
    def __init__(self, name, ongoingBonus=1, ongoingBonusVS=None, discardEffect=None):
        self.name = name
        self.ongoingBonus = ongoingBonus
        if ongoingBonusVS is None:
            ongoingBonusVS = []
        self.ongoingBonusVS = ongoingBonusVS
        self.discardEffect = discardEffect


class FKCCard:
    def __init__(
        self,
        name,
        ongoingBonus=1,
        ongoingEffect=None,
        ongoingBonusVS=None,
        discardEffect=None,
    ):
        self.name = name
        self.ongoingBonus = ongoingBonus
        if ongoingBonusVS is None:
            ongoingBonusVS = []
        self.ongoingBonusVS = ongoingBonusVS
        self.ongoingEffect = ongoingEffect
        self.discardEffect = discardEffect


class Option:
    def __init__(self, name, card, pc, helpers=None, lookAhead=True):
        self.name = name
        self.card = card  # either a challenge card or a choice to skip a challenge
        self.pc = pc
        if helpers is None:
            helpers = []
        self.helpers = helpers
        self.priority = 0  # non-challenge card option priority goes here
        self.tiebreaker = 0
        if isinstance(card, ChallengeCard):
            self.priority = getPriority(card, pc)
            if lookAhead:  # look ahead one turn
                copyState()
                # adjudicate the action, assume most likely event happens (50/50 = success),
                # update things in futureState, then generate Options (minus this one
                # if success) and get the greatest priority of the next player.
                # Add that to this priority. Of course use Option(... lookAhead=False)
            self.tiebreaker = pc.totalStrength(card) - card.storyBonus

    def __eq__(self, obj):
        return self.priority == obj.priority and self.tiebreaker == obj.tiebreaker

    def __lt__(self, obj):
        return self.priority < obj.priority or (
            self.priority == obj.priority and self.tiebreaker < obj.tiebreaker
        )

    def __gt__(self, obj):
        return self.priority > obj.priority or (
            self.priority == obj.priority and self.tiebreaker > obj.tiebreaker
        )

    def __le__(self, obj):
        return self.priority <= obj.priority or (
            self.priority == obj.priority and self.tiebreaker <= obj.tiebreaker
        )

    def __ge__(self, obj):
        return self.priority >= obj.priority or (
            self.priority == obj.priority and self.tiebreaker >= obj.tiebreaker
        )

    def takeAction(self):
        if isinstance(self.card, ChallengeCard):
            currentDeck = getDeckFromType(self.card.currentDeck)

            helperBonus = 0
            for helper in self.helpers:
                # handle assist tokens, discarded card effects
                # assists are probably just names of PCs
                # others can be names of discarded FKC or Surprise cards
                # for assists, apply the bonus then flip that character's
                # 'hasToken' flag to False
                pass
            # small delta is good
            adjustedDelta = getDelta(self.card, self.pc) - helperBonus
            prob = getProbFromDelta(adjustedDelta)

            diceroll = random.random()
            if self.card.effect == "roll twice pick worst":
                diceroll = max(diceroll, random.random())
            if self.card.effect == "roll twice pick best":
                diceroll = min(diceroll, random.random())
            if self.card.effect == "spend action token to engage":
                self.pc.hasToken = False

            if diceroll < prob:
                print("Success!\n")
                self.card.diffMod = 0
                self.card.damageMod = 0
                if self.card.succeedEffect == "flip self":
                    currentDeck[0] = currentDeck[0].reverse
                else:
                    currentDeck.remove(self.card)
                    self.pc.lootCards.append(self.card)
                if self.card.succeedEffect == "flip next":
                    currentDeck[0] = currentDeck[0].reverse
                if self.card.succeedEffect == "flip next recover 1":
                    currentDeck[0] = currentDeck[0].reverse
                    state.health = max(state.health + 1, state.maxHealth)
                if self.card.succeedEffect == "flip villain":
                    state.villainDeck[0] = state.villainDeck[0].reverse
                    state.villainDeck[0].reveal()
                if self.card.succeedEffect == "flip relic":
                    state.relicDeck[0] = state.relicDeck[0].reverse
                    state.relicDeck[0].reveal()
                if self.card.succeedEffect == "flip location":
                    state.locationDeck[0] = state.locationDeck[0].reverse
                    state.locationDeck[0].reveal()
                if self.card.succeedEffect == "return top discarded challenge":
                    if state.challengeDiscard:
                        returnedCard = state.challengeDiscard.pop()
                        returnedDeck = getDeckFromType(returnedCard.decktype)
                        returnedCard.reveal()
                        returnedDeck.insert(0, returnedCard)
                currentDeck[0].reveal()  # whether new card or flipped

            else:
                print("Failure.\n")
                state.health -= self.card.getDamage()
                if self.card.failEffect == "flip self":
                    currentDeck[0] = currentDeck[0].reverse
                    currentDeck[0].reveal()
                if self.card.failEffect == "flip villain":
                    state.villainDeck[0] = state.villainDeck[0].reverse
                    state.villainDeck[0].reveal()
                if self.card.failEffect == "flip relic":
                    state.relicDeck[0] = state.relicDeck[0].reverse
                    state.relicDeck[0].reveal()
                if self.card.failEffect == "flip location":
                    state.locationDeck[0] = state.locationDeck[0].reverse
                    state.locationDeck[0].reveal()
                if self.card.failEffect == "difficulty down 2":
                    self.card.diffMod -= 2
                if self.card.failEffect == "damage up 2":
                    self.card.damageMod += 2
                if self.card.failEffect == "succeed after damage":
                    currentDeck.remove(self.card)
                    self.pc.lootCards.append(self.card)
                    currentDeck[0].reveal()
            nextPlayer()


#############
# Functions #
#############

# def rollTAZ20():
#     sequence = [-100, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4, 4, 4, 5, 5, 5, 6, 6, 6, 100]
#     return random.choice(sequence)


def getProb(card, pc):
    delta = getDelta(card, pc)
    return getProbFromDelta(delta)


def getDelta(card, pc):
    strength = pc.totalStrength(card)
    difficulty = card.getDifficulty()
    return difficulty - strength


def getProbFromDelta(delta):
    if delta > 6:
        return 0.05
    if delta < 2:
        return 0.95
    return {
        2: 0.8,
        3: 0.65,
        4: 0.5,
        5: 0.35,
        6: 0.2,
    }.get(delta, 0)


def getProbPercentile(card, pc):
    prob = getProb(card, pc)
    return prob * 100


def getDeckFromType(decktype):
    if decktype == "villain":
        return state.villainDeck
    if decktype == "relic":
        return state.relicDeck
    if decktype == "location":
        return state.locationDeck
    return None


def getDeckClearPriorities(decktype):
    c1a = state.priorities["clear 1 card a"]
    c1b = state.priorities["clear 1 card b"]
    if oneDeckClear():
        if (oneDeckClear() in ["villain", "location"] and decktype == "relic") or (
            oneDeckClear() == "relic"
        ):
            c1a = state.priorities["clear 1 card increased priority a"]
        else:
            c1a = state.priorities["clear 1 card reduced priority a"]
    return c1a, c1b


def getOutcomes(challenge, currentPlayerHasLoot2Card=False):
    if challenge is None:
        return 0, 0
    c1a, c1b = getDeckClearPriorities(challenge.currentDeck)

    hca = state.priorities["health change a"]
    hcb = state.priorities["health change b"]

    ntrf = state.priorities["next turn relevance factor"]

    currentDeck = getDeckFromType(challenge.currentDeck)

    currentHealth = state.health
    newHealth = max(currentHealth - challenge.getDamage(), 0)

    success = challenge.loot + c1a / (len(currentDeck) + c1b)
    if currentPlayerHasLoot2Card and challenge.loot == 2:
        success = 1 + c1a / (len(currentDeck) + c1b)
    failure = hca * (1 / (currentHealth + hcb) - 1 / (newHealth + hcb))

    # todo: put all of these in priorities.yaml

    succeedEffectFactor = 0
    if challenge.succeedEffect == "return top discarded challenge":
        if state.challengeDiscard:
            returnedCard = state.challengeDiscard[-1]
            returnedDeck = getDeckFromType(returnedCard.decktype)
            c1a2, c1b2 = getDeckClearPriorities(returnedCard.currentDeck)
            simplifiedCurrentSuccess = c1a2 / (len(returnedDeck) + c1b2)
            simplifiedFutureSuccess = c1a2 / (len(returnedDeck) + 1 + c1b2)
            succeedEffectFactor = (
                ntrf * 0.5 * (simplifiedFutureSuccess - simplifiedCurrentSuccess)
            )
    if challenge.succeedEffect == "flip next recover 1":
        newHealthAfterRecover = max(currentHealth + 1, state.maxHealth)
        succeedEffectFactor = hca * (
            1 / (currentHealth + hcb) - 1 / (newHealthAfterRecover + hcb)
        )

    failEffectFactor = 0
    if challenge.failEffect == "difficulty down 2":
        # value of this failEffect goes down as it becomes more attainable
        difficulty = challenge.getDifficulty()
        if difficulty > 8:
            chanceIncrease = 0.3
        elif difficulty < 4:
            chanceIncrease = 0
        else:
            chanceIncrease = 0.15
        failEffectFactor = chanceIncrease * (success - failure)
    if challenge.failEffect == "succeed after damage":
        failEffectFactor = success
    if challenge.failEffect == "damage up 2":
        newHealthFailNextTurn = max(currentHealth - challenge.getDamage() - 2, 0)
        futureFailure = hca * (
            1 / (currentHealth + hcb) - 1 / (newHealthFailNextTurn + hcb)
        )
        failEffectFactor = ntrf * 0.5 * (futureFailure - failure)
    if challenge.failEffect == "flip self":
        # averaged cult/idol 2 cards, assumed 80% chance on front side
        # average 2 card is 2 points higher in difficulty (30% lower chance)
        # does 3 points of damage, and gives 1 more loot
        newHealthFailNextTurn = max(currentHealth - 3, 0)
        avgBackSuccess = (challenge.loot + 1) + c1a / (len(currentDeck) + c1b)
        avgBackFailure = hca * (
            1 / (currentHealth + hcb) - 1 / (newHealthFailNextTurn + hcb)
        )
        failEffectFactor = ntrf * (
            0.50 * (avgBackSuccess)
            + 0.50 * (avgBackFailure)
            - 0.80 * (success)
            - 0.20 * (failure)
        )

    success += succeedEffectFactor
    failure += failEffectFactor

    return success, failure


def oneDeckClear():
    if state.villainDeck[0].finale and state.villainDeck[0].difficulty == 0:
        return "villain"
    if state.relicDeck[0].finale and state.relicDeck[0].difficulty == 0:
        return "relic"
    if state.locationDeck[0].finale and state.locationDeck[0].difficulty == 0:
        return "location"

    return False


def getAdjacentCards(challenge):
    leftCard = rightCard = None
    if challenge.currentDeck == "villain":
        rightCard = state.relicDeck[0]
    if challenge.currentDeck == "relic":
        leftCard = state.villainDeck[0]
        rightCard = state.locationDeck[0]
    if challenge.currentDeck == "location":
        leftCard = state.relicDeck[0]
    return leftCard, rightCard


def getPriority(challenge, pc):
    delta = getDelta(challenge, pc)
    # this is to treat loot 2 cards on the board as loot 1 if the player
    # already has a loot 2 card
    currentPlayerHasLoot2Card = pc.lootCards and pc.lootCards[0].loot == 2
    success, failure = getOutcomes(challenge, currentPlayerHasLoot2Card)
    prob = getProb(challenge, pc)

    leftCard, rightCard = getAdjacentCards(challenge)
    leftSuccess, leftFailure = getOutcomes(leftCard)
    rightSuccess, rightFailure = getOutcomes(rightCard)

    diffFactor = (
        state.priorities["adjacent difficulty factor"]
        * 0.15
        * (
            challenge.leftDiff * (leftSuccess - leftFailure)
            + challenge.rightDiff * (rightSuccess - rightFailure)
        )
    )

    ### testing
    # leftCardName = leftCard.name if leftCard is not None else "None"
    # rightCardName = rightCard.name if rightCard is not None else "None"
    # print(f">>>{challenge.name}: {success}, {failure}, {diffFactor}")
    # print(f">>>>{leftCardName}, {rightCardName}")
    ###

    return prob * success + (1 - prob) * failure + diffFactor


def nextPlayer():
    state.currentPlayer += 1
    if state.currentPlayer >= len(state.players):
        state.currentPlayer = 0
        for player in state.players:
            player.hasToken = True


def copyState():
    futureState.villain = state.villain
    futureState.relic = state.relic
    futureState.location = state.location
    futureState.health = state.health
    futureState.maxHealth = state.maxHealth
    futureState.currentPlayer = state.currentPlayer
    futureState.relicTokens = state.relicTokens
    futureState.villainDeck = copy.deepcopy(state.villainDeck)
    futureState.relicDeck = copy.deepcopy(state.relicDeck)
    futureState.locationDeck = copy.deepcopy(state.locationDeck)
    futureState.challengeDiscard = copy.deepcopy(state.challengeDiscard)
    futureState.surprise = copy.deepcopy(state.surprise)
    futureState.players = copy.deepcopy(state.players)
    futureState.priorities = copy.deepcopy(state.priorities)
