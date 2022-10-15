import random
import math
import copy
import state, futureState


###########
# Classes #
###########


class PlayerCharacter:
    def __init__(self, name):
        if name.lower() not in ["warrior", "rogue", "priest", "bard", "wizard"]:
            raise ValueError(f"Invalid class name: {name}")
        self.name = name.lower()
        self.lootCards = []
        self.fkcCards = []
        self.hasToken = True
        self.assistAfter = 2 if self.name == "priest" else 1
        self.assistBefore = 2
        if self.name == "bard":
            self.assistBefore = 1
        if self.name == "rogue":
            self.assistBefore = 3

    def baseStrength(self, challengeCard):
        returnval = 4

        if "baseStrength always 4" in [
            fkcCard.ongoingEffect for fkcCard in self.fkcCards
        ]:
            return 4

        if self.name == "warrior" and "monster" not in challengeCard.icons:
            returnval = 2
        if self.name == "rogue" and "trap" not in challengeCard.icons:
            returnval = 2
        if self.name == "priest" and "spooky" not in challengeCard.icons:
            returnval = 2
        if self.name == "wizard" and "magic" not in challengeCard.icons:
            returnval = 1
        if self.name == "bard" and challengeCard.decktype != "relic":
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
        return totalStrength

    def getAssist(self, stat, challengeCardIcons=None):
        assist = stat
        if "+1 assist any challenge" in [
            fkcCard.ongoingEffect for fkcCard in self.fkcCards
        ]:
            assist += 1
        if "+1 assist monster challenge" in [
            fkcCard.ongoingEffect for fkcCard in self.fkcCards
        ]:
            if challengeCardIcons is None:  # unspecified challenge
                assist += 0.25
            elif "monster" in challengeCardIcons:
                assist += 1
        if state.villain == "giant":
            assist += 1
        return assist

    def getAssistAfter(self, challengeCardIcons=None):
        return self.getAssist(self.assistAfter, challengeCardIcons)

    def getAssistBefore(self, challengeCardIcons=None):
        return self.getAssist(self.assistBefore, challengeCardIcons)

    def addFkcCard(self, newFkcCard):
        # give 'spend token' cards to the bard
        if "spend token" in newFkcCard.ongoingEffect and self.name != "bard":
            bardPlayer = getPlayerCharacter("bard")
            if bardPlayer is not None:
                if (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in bardPlayer.fkcCards]
                    or len(bardPlayer.fkcCards) < 2
                ):
                    bardPlayer.addFkcCard(newFkcCard)
                    return
        # don't give glutton's fork to the priest
        if (
            newFkcCard.ongoingEffect == "spend token recover 1"
            and self.name == "priest"
        ):
            notAPriest = None
            for player in state.players:
                if player.name != "priest" and (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                    or len(player.fkcCards) < 2
                ):
                    notAPriest = player
                    break
            if notAPriest is not None:
                notAPriest.addFkcCard(newFkcCard)
                return
            else:
                # nobody can take this, just discard it.
                newFkcCard.discard()
                return
        if (
            "no fkc card limit" in [fkcCard.ongoingEffect for fkcCard in self.fkcCards]
            or len(self.fkcCards) < 2
        ):
            newFkcCard.pc = self
            self.fkcCards.append(newFkcCard)
        else:
            # try to give the card to someone else
            for player in state.players:
                if player != self and (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                    or len(player.fkcCards) < 2
                ):
                    player.addFkcCard(newFkcCard)
                    return
            # if not possible, discard least valuable and/or best discard effect
            newFkcCard.pc = self
            self.fkcCards.append(newFkcCard)
            mostDiscardable = newFkcCard
            for fkcCard in self.fkcCards:
                if fkcCard.discardPriorityEOT() > mostDiscardable.discardPriorityEOT():
                    mostDiscardable = fkcCard
            mostDiscardable.discard()

    def drawFkcCard(self):
        fkcCard = state.fkcDeck.pop()
        if self.name == "rogue":
            fkcCard2 = state.fkcDeck.pop()
            if fkcCard.getHoldPriority() > fkcCard2.getHoldPriority():
                self.addFkcCard(fkcCard)
                fkcCard2.discard(skipDiscardEffect=True)
            else:
                self.addFkcCard(fkcCard2)
                fkcCard.discard(skipDiscardEffect=True)
        else:
            self.addFkcCard(fkcCard)

    def addLootCard(self, newLootCard):
        if newLootCard.loot >= 3:
            state.challengeDiscard.append(newLootCard)
            self.drawFkcCard()
        elif newLootCard.loot == 2:
            otherCard = None
            for lootCard in self.lootCards:
                if lootCard.loot == 1:
                    otherCard = lootCard
                    break
            for lootCard in self.lootCards:
                if lootCard.loot == 2:
                    otherCard = lootCard
                    break
            if otherCard is not None:
                self.lootCards.remove(otherCard)
                state.challengeDiscard.append(newLootCard)
                state.challengeDiscard.append(otherCard)
                self.drawFkcCard()
            else:
                self.lootCards.append(newLootCard)
        elif newLootCard.loot == 1:
            otherCard = None
            for lootCard in self.lootCards:
                if lootCard.loot == 2:
                    otherCard = lootCard
                    break
            if otherCard is not None:
                self.lootCards.remove(otherCard)
                state.challengeDiscard.append(newLootCard)
                state.challengeDiscard.append(otherCard)
                self.drawFkcCard()
            else:
                otherCard = None
                otherCard2 = None
                for lootCard in self.lootCards:
                    if lootCard.loot == 1:
                        if otherCard is None:
                            otherCard = lootCard
                        else:
                            otherCard2 = lootCard
                            break
                if otherCard2 is not None:
                    self.lootCards.remove(otherCard)
                    self.lootCards.remove(otherCard2)
                    state.challengeDiscard.append(newLootCard)
                    state.challengeDiscard.append(otherCard)
                    state.challengeDiscard.append(otherCard2)
                    self.drawFkcCard()
                else:
                    self.lootCards.append(newLootCard)

    def getHoldTokenPriority(self, localState=state):
        # Priority for a given player to hold their token
        # if not self.hasToken:
        #     return 100
        if self.name == "bard":
            return 0

        playerNumber = 0
        for index, player in enumerate(localState.players):
            if player == self:
                playerNumber = index
                break

        holdPriority = 0.01  # just so bard shows up first in priority

        turnsRemaining = len(localState.players) - 1 - localState.currentPlayer
        assistOpportunities = getNumberOfAssistOpportunities(turnsRemaining)
        otherTokensAvailable = len(
            [True for player in localState.players if player.hasToken]
        )
        holdPriority += (
            0.3
            * (self.getAssistBefore() + self.getAssistAfter())
            * max(assistOpportunities - otherTokensAvailable, 0)
        )
        myTurnIsComingUp = localState.currentPlayer < playerNumber
        if myTurnIsComingUp:
            n = 0
            if self.name in ["wizard", "priest"]:
                n += 1
            if self.name == "warrior":
                n += 0.5  # warrior's ability not as valuable
            for fkcCard in self.fkcCards:
                if "spend token" in fkcCard.ongoingEffect:
                    n += 1

            # holdPriority bonus = 1 when n = 1, approaches 2 as n increases
            # this is to indicate the value of saving your token until your turn
            holdPriority += (2 ** (1 - n)) * ((2**n) - 1)

        return holdPriority

    def getHoldPriority(self, currentDeck=None, localState=state):
        return self.getHoldTokenPriority(localState)


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
        self.effect = effect  # ongoing effect, not triggered by success or failure
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
            self.diffMod += random.choice(range(1, 7))
        if self.deck == "hoard" and self.effect == "add relic tokens to difficulty":
            self.diffMod += state.relicTokens

    def getDifficulty(self):
        return (
            self.difficulty
            + self.diffMod
            + cardBoost(self.decktype, "left")
            + cardBoost(self.decktype, "right")
        )

    def getDamage(self):
        return self.damage + self.damageMod


class SurpriseCard:
    def __init__(
        self,
        name,
        ongoingBonus=1,
        ongoingBonusVS=None,
        discardEffect="",
        currentDeck="",
    ):
        self.name = name
        self.ongoingBonus = ongoingBonus
        if ongoingBonusVS is None:
            ongoingBonusVS = []
        self.ongoingBonusVS = ongoingBonusVS
        self.discardEffect = discardEffect
        self.currentDeck = currentDeck
        self.reverse = self  # some challenge cards flip next
        self.ongoingEffect = ""
        self.effect = ""
        self.finale = False
        self.icons = []

    def reveal(self):
        currentDeck = getDeckFromType(self.currentDeck)
        currentDeck.remove(self)
        if state.surprise is None:
            state.surprise = self
        else:
            if self.discardPriorityEOT() > state.surprise.discardPriorityEOT():
                self.discard()
            else:
                state.surprise.discard()
                state.surprise = self
        currentDeck[0].reveal()

    def discardPriorityEOT(self):
        recoverPriority = getRecoverPriority(3)
        # Should be 4.2 if healing from 7 to 10; 2.4 if healing from 8 to 10; 1.1 if healing from 9 to 10

        flipPriority = 0
        activeCards = getActiveCards()
        for card in activeCards:
            # TODO: consider also flipping if none of the current challenge cards are strong vs
            if card.deck in ["cult", "idol"] and card.number == 2:
                flipPriority += 1

        regainTokenPriority = 0
        turnsRemaining = len(state.players) - 1 - state.currentPlayer
        assistOpportunities = getNumberOfAssistOpportunities(turnsRemaining)
        assistTokensAvailable = len(
            [True for player in state.players if player.hasToken]
        )
        assistTokensExpended = len(state.players) - assistTokensAvailable
        regainTokenPriority = 0.5 * min(
            max(assistOpportunities - assistTokensAvailable, 0), assistTokensExpended
        )
        discardPriority = {
            "recover 3": recoverPriority,
            "draw fkc card": 3,
            "draw fkc card skip challenge": 0.5,  # better to use during turn
            "flip any active challenge cards": flipPriority,
            "regain action tokens": regainTokenPriority,
        }.get(self.discardEffect, 0)

        discardPriority -= self.getHoldPriority()

        return discardPriority

    def getHoldPriority(self, currentDeck=None, localState=state):
        holdPriority = 0
        if "any" in self.ongoingBonusVS:
            holdPriority = getSurpriseOngoingPriority(any=True)
        elif self.ongoingBonusVS:
            holdPriority = getSurpriseOngoingPriority()
        if (
            currentDeck is not None
            and len(currentDeck) > 1
            and isinstance(currentDeck[1], SurpriseCard)
        ):
            # about to uncover another surprise card, might as well use this one
            return 0
        return holdPriority

    def discard(self):
        if self == state.surprise:
            state.surprise = None
        state.surpriseDiscard.append(self)
        if self.discardEffect == "regain action tokens":
            for player in state.players:
                player.hasToken = True
        if self.discardEffect == "recover 3":
            state.health = min(state.health + 3, state.maxHealth)
        if self.discardEffect == "no damage after fail":
            state.pendingDamage = 0
        if self.discardEffect in ["draw fkc card", "draw fkc card skip challenge"]:
            newFkcCard = state.fkcDeck.pop()
            state.players[state.currentPlayer].addFkcCard(newFkcCard)
        if self.discardEffect == "flip any active challenge cards":
            activeCards = activeCards()
            for card in activeCards:
                if (
                    card.deck in ["cult", "idol"]
                    and card.number == 2
                    and not card.finale
                ):
                    card = card.reverse
        if self.discardEffect == "+2 any die roll suffer 1 damage":
            state.health -= 1

    def getAssistAfter(self, icons=None):
        if icons == None:
            icons = []
        if self.discardEffect == "+2 trap die roll" and "trap" in icons:
            return 2
        if self.discardEffect == "+2 magic die roll" and "magic" in icons:
            return 2
        if self.discardEffect == "+2 monster die roll" and "monster" in icons:
            return 2
        if self.discardEffect == "+2 spooky die roll" and "spooky" in icons:
            return 2
        if self.discardEffect == "+2 any die roll suffer 1 damage":
            return 2
        if self.discardEffect == "+1 any die roll":
            return 1
        return 0

    def getAssistBefore(self, icons=None):
        return 0


class FKCCard:
    def __init__(
        self,
        name,
        ongoingBonus=1,
        ongoingEffect="",
        ongoingBonusVS=None,
        discardEffect="",
        pc=None,
    ):
        self.name = name
        self.ongoingBonus = ongoingBonus
        if ongoingBonusVS is None:
            ongoingBonusVS = []
        self.ongoingBonusVS = ongoingBonusVS
        self.ongoingEffect = ongoingEffect
        self.discardEffect = discardEffect
        self.pc = pc

    def discardPriorityEOT(self):
        recover3Priority = getRecoverPriority(3)
        # Should be 4.2 if healing from 7 to 10; 2.4 if healing from 8 to 10; 1.1 if healing from 9 to 10
        recover2Priority = getRecoverPriority(2)

        regainTokenPriority = 0
        turnsRemaining = len(state.players) - 1 - state.currentPlayer
        assistOpportunities = getNumberOfAssistOpportunities(turnsRemaining)
        assistTokensAvailable = len(
            [True for player in state.players if player.hasToken]
        )
        assistTokensExpended = len(state.players) - assistTokensAvailable
        regainTokenPriority = 0.5 * min(
            max(assistOpportunities - assistTokensAvailable, 0), assistTokensExpended
        )
        ogba = state.priorities["ongoing bonus any"]
        ogb = state.priorities["ongoing bonus"]
        discardPriority = {
            "recover 3": recover3Priority,
            "recover 2": recover2Priority,
            "regain action tokens": regainTokenPriority,
        }.get(self.discardEffect, 0)

        discardPriority -= self.getHoldPriority()

        return discardPriority

    def getHoldPriority(self, currentDeck=None, localState=state):
        ogba = state.priorities["ongoing bonus any"]
        ogb = state.priorities["ongoing bonus"]
        recover3Priority = getRecoverPriority(3)

        holdPriority = 0
        if "any" in self.ongoingBonusVS:
            holdPriority += ogba * self.ongoingBonus
        elif self.ongoingBonusVS:
            holdPriority += self.ongoingBonus * (
                ogb + (len(self.ongoingBonusVS) - 1) * (ogba - ogb) / 3.0
            )
        # todo: add these to priorities.yaml
        ongoingEffectValue = {
            "no fkc card limit": 100,  # don't discard fannypack!
            "spend token recover 1": 3,
            "+1 assist monster challenge": (ogba - ogb) / 4.0,
            "baseStrength always 4": ogba,
            "+2 trap die roll when spend token": ogb,
            "no assist": -3,
            "assist self": ogb,
            "no damage after fail but discard this": recover3Priority,
            "+1 assist any challenge": (ogba - ogb) / 3.0,
            "recover 1 skip challenge": 6,
            "spend token after fail reduce damage by 2 any player": 10,
            "spend token after fail reduce damage by 1": 4,
            "+1 when difficulty greater than 9": ogb,
            "can use other players abilities": ogb,
            "after fail reduce damage by 1": 8,
        }.get(self.ongoingEffect, 0)

        holdPriority += ongoingEffectValue

        discardEffectValue = {
            "win monster challenge": ogba * 2,
            "+3 any die roll before": ogba,
            "+3 monster die roll any player": ogba,
            "any challenge 50%": ogb,
        }.get(self.discardEffect, 0)

        holdPriority += discardEffectValue
        return holdPriority

    def discard(self, skipDiscardEffect=False):
        if self.pc is not None:
            self.pc.fkcCards.remove(self)
        self.pc = None
        state.fkcDiscard.append(self)

        if not skipDiscardEffect:
            if self.discardEffect == "regain action tokens":
                for player in state.players:
                    player.hasToken = True
            if self.discardEffect == "recover 3":
                state.health = min(state.health + 3, state.maxHealth)
            if self.discardEffect == "recover 2":
                state.health = min(state.health + 2, state.maxHealth)
            if self.discardEffect == "no damage after fail any player":
                state.pendingDamage = 0

    def getAssistAfter(self, icons=None):
        if icons == None:
            icons = []
        if (
            self.discardEffect == "+3 monster die roll any player"
            and "monster" in icons
        ):
            return 3
        if (
            self.discardEffect == "+2 monster die roll any player"
            and "monster" in icons
        ):
            return 2
        if self.discardEffect == "+2 spooky die roll any player" and "spooky" in icons:
            return 2
        if self.discardEffect == "+2 trap die roll any player" and "trap" in icons:
            return 2
        if self.discardEffect == "+2 magic die roll any player" and "magic" in icons:
            return 2
        if self.discardEffect == "+2 any die roll any player":
            return 2
        if self.discardEffect == "+1 any die roll any player":
            return 1
        return 0

    def getAssistBefore(self, icons=None):
        if self.discardEffect == "+3 any die roll before":
            return 3
        return 0


class Option:
    def __init__(self, card, pc, helpers=None, lookAhead=True):
        self.pc = pc
        self.name = card.name if card is not None else ""
        self.card = card  # either a challenge card or a choice to skip a challenge
        if helpers is None:
            helpers = []
        self.helpers = helpers
        self.priority = 0  # non-challenge card option priority goes here
        self.success = 0
        self.failure = 0
        self.assists = 0
        if isinstance(card, ChallengeCard):
            self.priority, self.success, self.failure = getPriority(
                card, pc, helpers, lookAhead
            )
            if lookAhead and not oneDeckClear():  # look ahead one turn
                # adjudicate the action, assume success,
                # update things in futureState, then generate Options (minus this one)
                # and get the greatest priority of the next player.
                # Add that to this priority.
                copyState()
                currentDeck = getDeckFromType(self.card.currentDeck)
                self.handleSuccessFutureState(currentDeck)
                if not futureState.won:
                    futureOptions = assembleOptions(
                        localState=futureState, currentDeckName=self.card.currentDeck
                    )
                    if futureOptions:
                        self.priority += (
                            state.priorities["next turn relevance factor"]
                            * futureOptions[0].priority
                        )

        elif card is not None:
            if card.discardEffect == "draw fkc card skip challenge":
                self.priority = 2.5
            if card.ongoingEffect == "recover 1 skip challenge":
                self.priority = getRecoverPriority(1)

    def __eq__(self, obj):
        return self.priority == obj.priority

    def __lt__(self, obj):
        return self.priority < obj.priority

    def __gt__(self, obj):
        return self.priority > obj.priority

    def __le__(self, obj):
        return self.priority <= obj.priority

    def __ge__(self, obj):
        return self.priority >= obj.priority

    def handleSuccess(self, currentDeck):
        # Todo: add the rest
        if state.display:
            print("\033[92mSuccess!\033[0m\n")
        self.card.diffMod = 0
        self.card.damageMod = 0
        if self.card.finale:
            self.pc.drawFkcCard()
        if self.card.succeedEffect == "flip self" or self.card.finale:
            currentDeck[0] = currentDeck[0].reverse
        else:
            currentDeck.remove(self.card)
            self.pc.addLootCard(self.card)
        if self.card.succeedEffect == "flip next":
            if not currentDeck[0].finale:
                currentDeck[0] = currentDeck[0].reverse
        if self.card.succeedEffect == "flip next recover 1":
            if not currentDeck[0].finale:
                currentDeck[0] = currentDeck[0].reverse
            state.health = min(state.health + 1, state.maxHealth)
        if self.card.succeedEffect == "flip villain":
            if not state.villainDeck[0].finale:
                state.villainDeck[0] = state.villainDeck[0].reverse
                state.villainDeck[0].reveal()
        if self.card.succeedEffect == "flip relic":
            if not state.relicDeck[0].finale:
                state.relicDeck[0] = state.relicDeck[0].reverse
                state.relicDeck[0].reveal()
        if self.card.succeedEffect == "flip location":
            if not state.locationDeck[0].finale:
                state.locationDeck[0] = state.locationDeck[0].reverse
                state.locationDeck[0].reveal()
        if self.card.succeedEffect == "return top discarded challenge":
            if state.challengeDiscard:
                # todo: check this
                returnedCard = state.challengeDiscard.pop()
                returnedDeck = getDeckFromType(returnedCard.decktype)
                returnedCard.reveal()
                returnedDeck.insert(0, returnedCard)
        currentDeck[0].reveal()  # whether new card or flipped
        self.handleEndOfTurn()

    def handleSuccessFutureState(self, currentDeck):
        for helper in self.helpers:
            if isinstance(helper, PlayerCharacter):
                getPlayerCharacter(helper.name, futureState).hasToken = False
            elif isinstance(helper, Ability):
                if helper.name == "wizard ability" and "monster" in self.card.icons:
                    getPlayerCharacter(self.pc.name, futureState).hasToken = False
                if helper.name == "warrior ability":
                    futureState.health -= 1
                    getPlayerCharacter(self.pc.name, futureState).hasToken = False
            elif isinstance(helper, SurpriseCard):
                futureState.surprise = None
            else:
                futurePC = getPlayerCharacter(self.pc.name, futureState)
                for fkcCard in futurePC.fkcCards:
                    if fkcCard.discardEffect == helper.discardEffect:
                        futurePC.fkcCards.remove(fkcCard)

        if self.card.succeedEffect == "flip next recover 1":
            futureState.health = min(futureState.health + 1, futureState.maxHealth)
        if self.card.succeedEffect == "flip villain":
            if not futureState.villainDeck[0].finale:
                futureState.villainDeck[0] = futureState.villainDeck[0].reverse
                futureState.villainDeck[0].reveal()
        if self.card.succeedEffect == "flip relic":
            if not futureState.relicDeck[0].finale:
                futureState.relicDeck[0] = futureState.relicDeck[0].reverse
                futureState.relicDeck[0].reveal()
        if self.card.succeedEffect == "flip location":
            if not futureState.locationDeck[0].finale:
                futureState.locationDeck[0] = futureState.locationDeck[0].reverse
                futureState.locationDeck[0].reveal()
        self.handleEndOfTurn(futureState)

    def handleFailure(self, currentDeck):
        # TODO
        self.handleEndOfTurn()

    def handleEndOfTurn(self, localState=state):
        # Healing and other end-of-turn things
        # tokens first.
        # after that, consider end-of-turn discard effects
        if (
            localState.relicDeck[0].finale
            and localState.relicDeck[0].difficulty == 0
            and (
                (
                    localState.locationDeck[0].finale
                    and localState.locationDeck[0].difficulty == 0
                )
                or (
                    localState.villainDeck[0].finale
                    and localState.villainDeck[0].difficulty == 0
                )
            )
        ):
            localState.won = True
            return

        pc = self.pc
        if localState == futureState:
            pc = getPlayerCharacter(self.pc.name, futureState)

        if (
            pc.name == "priest"
            or (
                "can use other players abilities"
                in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
                and "priest" in [player.name for player in localState.players]
            )
            or "spend token recover 1"
            in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
        ) and pc.hasToken:
            healPriority = getRecoverPriority(1, localState)
            if healPriority > pc.getHoldTokenPriority(localState):
                if localState == state and state.display:
                    print("Healing for 1...")
                localState.health = min(localState.health + 1, localState.maxHealth)
                pc.hasToken = False
        for player in localState.players:
            for fkcCard in player.fkcCards:
                if fkcCard.discardPriorityEOT() > 0 and not (
                    (
                        "recover 3" == fkcCard.discardEffect
                        and localState.maxHealth - localState.health < 3
                    )
                    or (
                        "recover 2" == fkcCard.discardEffect
                        and localState.maxHealth - localState.health < 2
                    )
                ):
                    if localState == state and state.display:
                        print(f"Discarding {fkcCard.name}...")
                    fkcCard.discard()
        if (
            localState.surprise is not None
            and localState.surprise.discardPriorityEOT() > 0.5
        ):
            if localState == state and state.display:
                print(f"Discarding {localState.surprise.name}...")
            localState.surprise.discard()
        nextPlayer(localState)

    def tryAfterRollHelpers(
        self, maxAssists, prob, adjustedDelta, diceroll, currentDeck, minimumNeeded
    ):
        # "arma" stands for "after roll max assists", excludes assists used before roll
        arma = maxAssists - self.assists
        afterRollAssists = 0
        potentialHelpers = []
        if state.surprise is not None and (
            "any die roll" in state.surprise.discardEffect
            or (
                "trap die roll" in state.surprise.discardEffect
                and "trap" in self.card.icons
            )
            or (
                "monster die roll" in state.surprise.discardEffect
                and "monster" in self.card.icons
            )
            or (
                "spooky die roll" in state.surprise.discardEffect
                and "spooky" in self.card.icons
            )
            or (
                "magic die roll" in state.surprise.discardEffect
                and "magic" in self.card.icons
            )
        ):
            potentialHelpers.append(state.surprise)
        for player in state.players:
            if (
                player.hasToken
                and (
                    "no assist"
                    not in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                )
                and (
                    player != self.pc
                    or "assist self"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                )
                and arma > 0
            ):
                potentialHelpers.append(player)
            for fkcCard in player.fkcCards:
                if (
                    "any die roll any player" in fkcCard.discardEffect
                    or (
                        "trap die roll any player" in fkcCard.discardEffect
                        and "trap" in self.card.icons
                    )
                    or (
                        "monster die roll any player" in fkcCard.discardEffect
                        and "monster" in self.card.icons
                    )
                    or (
                        "spooky die roll any player" in fkcCard.discardEffect
                        and "spooky" in self.card.icons
                    )
                    or (
                        "magic die roll any player" in fkcCard.discardEffect
                        and "magic" in self.card.icons
                    )
                ):
                    potentialHelpers.append(fkcCard)

        def makeSetsOfUsefulHelpers(setsOfUsefulHelpers, potentialHelpers, newSet):
            for index, potentialHelper in enumerate(potentialHelpers):
                newSet.append(potentialHelper)
                if (
                    len(
                        [
                            helper
                            for helper in newSet
                            if isinstance(helper, PlayerCharacter)
                        ]
                    )
                    <= arma
                ):
                    helpSum = sum(
                        [helper.getAssistAfter(self.card.icons) for helper in newSet]
                    )
                    if helpSum >= minimumNeeded:
                        setsOfUsefulHelpers.append(newSet.copy())
                    else:
                        makeSetsOfUsefulHelpers(
                            setsOfUsefulHelpers, potentialHelpers[index + 1 :], newSet
                        )
                newSet.pop()

        setsOfUsefulHelpers = []
        makeSetsOfUsefulHelpers(setsOfUsefulHelpers, potentialHelpers, [])
        setsOfUsefulHelpers = sorted(
            setsOfUsefulHelpers,
            key=lambda set: sum(
                [x.getHoldPriority(currentDeck=currentDeck) for x in set]
            ),
        )
        if (
            setsOfUsefulHelpers
            and sum([helper.getHoldPriority() for helper in setsOfUsefulHelpers[0]])
            < self.success - self.failure
        ):
            prob = getProbFromDelta(
                adjustedDelta
                - sum(
                    helper.getAssistAfter(self.card.icons)
                    for helper in setsOfUsefulHelpers[0]
                )
            )
            if diceroll < prob:
                for helper in setsOfUsefulHelpers[0]:
                    if isinstance(helper, PlayerCharacter):
                        helper.hasToken = False
                    else:
                        helper.discard()
                if state.display:
                    print("but with the help of...")
                    print(str([x.name for x in setsOfUsefulHelpers[0]]))
                self.handleSuccess(currentDeck)
                return True
        return False

    def takeAction(self):
        if self.card is None:
            self.handleEndOfTurn()
            return
        if isinstance(self.card, ChallengeCard):

            def getCardFromOngoing(effect, pc=self.pc):
                for card in pc.fkcCards:
                    if card.ongoingEffect == effect:
                        return card
                return None

            def getCardFromDiscard(effect, pc=self.pc):
                for card in pc.fkcCards:
                    if card.discardEffect == effect:
                        return card
                return None

            currentDeck = getDeckFromType(self.card.currentDeck)
            maxAssists = 1
            if "no assist" in self.card.icons:
                maxAssists = 0
            if "double assist" in self.card.icons:
                maxAssists = 2
            helperBonus = 0
            self.assists = 0
            useCoin = False
            for helper in self.helpers:
                # handle assist tokens, discarded card effects
                # The restrictions on how many pre-assists can happen
                # needs to be handled elsewhere, when assembling options
                if isinstance(helper, PlayerCharacter):
                    self.assists += 1
                    helperBonus += helper.getAssistBefore(self.card.icons)
                    helper.hasToken = False
                elif isinstance(helper, Ability):
                    if helper.name == "wizard ability" and "monster" in self.card.icons:
                        helperBonus += 3
                        self.pc.hasToken = False
                    if helper.name == "warrior ability":
                        helperBonus += 2
                        state.health -= 1
                        self.pc.hasToken = False
                else:
                    # Other helpers are FKC or Surprise cards to be discarded.
                    if (
                        helper.discardEffect == "win monster challenge"
                        and "monster" in self.card.icons
                    ):
                        helper.discard()
                        self.handleSuccess(currentDeck)
                        return
                    if helper.discardEffect == "+3 any die roll before":
                        helperBonus += 3
                    if helper.discardEffect == "any challenge 50%":
                        useCoin = True
                    helper.discard()

            # small delta is good
            adjustedDelta = getDelta(self.card, self.pc) - helperBonus
            prob = getProbFromDelta(adjustedDelta)

            diceroll = random.random()
            if useCoin:
                diceroll = random.choice([0.95, 0.05])
            else:
                if self.card.effect == "roll twice pick worst":
                    diceroll = max(diceroll, random.random())
                if self.card.effect == "roll twice pick best":
                    diceroll = min(diceroll, random.random())

            if self.card.effect == "spend action token to engage":
                self.pc.hasToken = False

            if diceroll < prob:
                # Success
                self.handleSuccess(currentDeck)
            else:
                # Failure
                if state.display:
                    print("\033[91mFailure.\033[0m\n")
                # Here is where we apply after-roll assists
                # or discard cards to improve roll result.
                # Compare self.success and self.failure, and compare
                # the difference in outcomes to the priority of keeping
                # a card or token.

                # first try scoundrels dice
                scoundrelsDice = None
                for player in state.players:
                    scoundrelsDice = getCardFromOngoing("reroll any player", player)
                    if scoundrelsDice is not None:
                        break
                if scoundrelsDice is not None:
                    if (
                        self.priority > scoundrelsDice.getHoldPriority()
                        and diceroll < 0.65
                    ):
                        if state.display:
                            print("trying scoundrel's dice...")
                        diceroll = random.random()
                        scoundrelsDice.discard()
                        if diceRoll < prob:
                            self.handleSuccess(currentDeck)
                            return
                        else:
                            if state.display:
                                print("no luck.")
                if diceroll < 0.95:

                    minimumNeeded = math.ceil((diceroll - prob) / 0.15)
                    helpersSuccessful = self.tryAfterRollHelpers(
                        maxAssists,
                        prob,
                        adjustedDelta,
                        diceroll,
                        currentDeck,
                        minimumNeeded,
                    )
                    if helpersSuccessful:
                        return  # This turns failure into success

                state.pendingDamage = self.card.getDamage()
                pendingHealth = state.health - state.pendingDamage
                # here is where you could discard a card to reduce damage

                # fkc cards first
                cloak = getCardFromOngoing("after fail reduce damage by 1")
                safetyHarness = getCardFromOngoing(
                    "no damage after fail but discard this"
                )
                slippies = getCardFromOngoing(
                    "spend token after fail reduce damage by 1"
                )
                shield = None
                for player in state.players:
                    shield = getCardFromOngoing(
                        "spend token after fail reduce damage by 2 any player", player
                    )
                    if shield is not None:
                        break

                phantomFist = None
                for player in state.players:
                    phantomFist = getCardFromDiscard(
                        "no damage after fail any player", player
                    )
                    if phantomFist is not None:
                        break

                while state.pendingDamage > 0:

                    if cloak is not None:
                        state.pendingDamage -= 1
                        cloak = None
                        continue

                    if safetyHarness is not None:
                        # player MUST discard safety harness in place of damage
                        safetyHarness.discard()
                        state.pendingDamage = 0
                        break

                    if (
                        state.pendingDamage == 1
                        and slippies is not None
                        and self.pc.hasToken
                    ):
                        # use slippies first if damage is only 1. Otherwise try shield first
                        useTokenPriority = getHealthChangePriority(
                            pendingHealth, pendingHealth + 1
                        )
                        keepTokenPriority = self.pc.getHoldTokenPriority()
                        if useTokenPriority > keepTokenPriority:
                            self.pc.hasToken = False
                            state.pendingDamage -= 1
                            slippies = None
                            continue

                    if shield is not None and shield.pc.hasToken:
                        useTokenPriority = getHealthChangePriority(
                            pendingHealth, min(pendingHealth + 2, state.health) + 1
                        )

                        keepTokenPriority = shield.pc.getHoldTokenPriority()
                        if useTokenPriority > keepTokenPriority:
                            shield.pc.hasToken = False
                            state.pendingDamage = max(state.pendingDamage - 2, 0)
                            shield = None
                            continue

                    if slippies is not None and self.pc.hasToken:
                        useTokenPriority = getHealthChangePriority(
                            pendingHealth, pendingHealth + 1
                        )
                        keepTokenPriority = self.pc.getHoldTokenPriority()
                        if useTokenPriority > keepTokenPriority:
                            self.pc.hasToken = False
                            state.pendingDamage -= 1
                            slippies = None
                            continue

                    if phantomFist is not None:
                        discardPriority = getHealthChangePriority(
                            pendingHealth, state.health
                        )
                        noDiscardPriority = state.priorities["ongoing bonus"]
                        if discardPriority > noDiscardPriority:
                            phantomFist.discard()
                            phantomFist = None
                            break
                    # end of our list of possibilities
                    break

                if (
                    state.surprise is not None
                    and state.surprise.discardEffect == "no damage after fail"
                ):
                    discardPriority = getHealthChangePriority(
                        pendingHealth, state.health
                    )
                    noDiscardPriority = getSurpriseOngoingPriority()
                    if (
                        self.card.failEffect == "succeed after damage"
                        and len(currentDeck) > 1
                        and isinstance(currentDeck[1], SurpriseCard)
                    ):
                        # if we're about to unveil another surprise card anyway
                        noDiscardPriority = 0
                    if discardPriority > noDiscardPriority:
                        state.surprise.discard()

                state.health = max(state.health - state.pendingDamage, 0)
                state.pendingDamage = 0
                if state.health < 1:
                    state.won = False
                    return
                if self.card.failEffect == "flip self":
                    currentDeck[0] = currentDeck[0].reverse
                    currentDeck[0].reveal()
                if self.card.failEffect == "flip villain":
                    if not state.villainDeck[0].finale:
                        state.villainDeck[0] = state.villainDeck[0].reverse
                        state.villainDeck[0].reveal()
                if self.card.failEffect == "flip relic":
                    if not state.relicDeck[0].finale:
                        state.relicDeck[0] = state.relicDeck[0].reverse
                        state.relicDeck[0].reveal()
                if self.card.failEffect == "flip location":
                    if not state.locationDeck[0].finale:
                        state.locationDeck[0] = state.locationDeck[0].reverse
                        state.locationDeck[0].reveal()
                if self.card.failEffect == "difficulty down 2":
                    self.card.diffMod -= 2
                if self.card.failEffect == "damage up 2":
                    self.card.damageMod += 2
                if self.card.failEffect == "succeed after damage":
                    currentDeck.remove(self.card)
                    self.pc.lootCards.append(self.card)
                    self.card.diffMod = 0
                    self.card.damageMod = 0
                    currentDeck[0].reveal()

                self.handleEndOfTurn()
        else:
            # Not a challenge card
            if self.card.discardEffect == "draw fkc card skip challenge":
                self.pc.drawFkcCard()
                self.card.discard()
            elif self.card.ongoingEffect == "recover 1 skip challenge":
                state.health = min(state.health + 1, state.maxHealth)
            self.handleEndOfTurn()


class Ability:
    def __init__(self, name, pc):
        self.name = name
        pcname = {
            "warrior ability": "warrior",
            "wizard ability": "wizard",
            "priest ability": "priest",
            "rogue ability": "rogue",
        }.get(name, "")
        self.pc = pc

    def getAssistBefore(self, icons):
        if self.name == "wizard ability" and "monster" in icons:
            return 3
        if self.name == "warrior ability":
            return 2
        return 0

    def getHoldPriority(self, currentDeck=None, localState=state):
        holdPriority = self.pc.getHoldPriority()
        if self.name == "warrior ability":
            holdPriority += getHealthChangePriority(
                max(localState.health - 1, 0), localState.health
            )
        return holdPriority

        # for helper in helpers:
        #     delta -= helper.getAssistBefore(challenge.icons)
        #     holdPriorityHelpers += helper.getHoldPriority()


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


def getDeckFromType(decktype, localState=state):
    if decktype == "villain":
        return localState.villainDeck
    if decktype == "relic":
        return localState.relicDeck
    if decktype == "location":
        return localState.locationDeck
    return None


def getPlayerCharacter(name, localState=state):
    for player in localState.players:
        if player.name == name:
            return player
    return None


def oneDeckClear(localState=state):
    if localState.villainDeck[0].finale and localState.villainDeck[0].difficulty == 0:
        return "villain"
    if localState.relicDeck[0].finale and localState.relicDeck[0].difficulty == 0:
        return "relic"
    if localState.locationDeck[0].finale and localState.locationDeck[0].difficulty == 0:
        return "location"

    return False


def getDeckClearPriorities(decktype, localState):
    c1a = state.priorities["clear 1 card a"]
    if decktype == "relic":
        c1a = c1a * 1.2
    c1b = state.priorities["clear 1 card b"]
    odc = oneDeckClear(localState)
    if odc:
        if (odc in ["villain", "location"] and decktype == "relic") or (odc == "relic"):
            c1a = state.priorities["clear 1 card increased priority a"]
            c1b = state.priorities["clear 1 card increased priority b"]
        else:
            c1a = state.priorities["clear 1 card reduced priority a"]
    return c1a, c1b


def getOutcomes(challenge, currentPlayerHasLoot2Card=False, localState=state):
    if challenge is None or (challenge.finale and challenge.difficulty == 0):
        return 0, 0

    ntrf = localState.priorities["next turn relevance factor"]

    currentDeck = getDeckFromType(challenge.currentDeck)

    # might consider using priorities.yaml for loot priority
    success = challenge.loot + getCardClearPriority(challenge.currentDeck, localState)
    if currentPlayerHasLoot2Card and challenge.loot == 2:
        success = 1 + getCardClearPriority(challenge.currentDeck, localState)
    failure = getDamagePriority(challenge.getDamage(), localState)

    # todo: put all of these in priorities.yaml

    succeedEffectFactor = 0
    if challenge.succeedEffect == "return top discarded challenge":
        if localState.challengeDiscard:
            returnedCard = localState.challengeDiscard[-1]
            returnedDeck = getDeckFromType(returnedCard.decktype, localState)
            simplifiedCurrentSuccess = getCardClearPriority(
                returnedCard.currentDeck, localstate, 0
            )
            simplifiedFutureSuccess = getCardClearPriority(
                returnedCard.currentDeck, localstate, 1
            )
            succeedEffectFactor = (
                ntrf * 0.5 * (simplifiedFutureSuccess - simplifiedCurrentSuccess)
            )
    if challenge.succeedEffect == "flip next recover 1":
        succeedEffectFactor = getRecoverPriority(1, localState)

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
        futureFailure = getDamagePriority(challenge.getDamage() + 2, localState)
        failEffectFactor = ntrf * 0.5 * (futureFailure - failure)
    if challenge.failEffect == "flip self":
        # averaged cult/idol 2 cards, assumed 80% chance on front side
        # average 2 card is 2 points higher in difficulty (30% lower chance)
        # does 3 points of damage, and gives 1 more loot
        avgBackSuccess = (challenge.loot + 1) + getCardClearPriority(
            challenge.currentDeck, localstate
        )
        avgBackFailure = getDamagePriority(3, localState)
        failEffectFactor = ntrf * (
            0.50 * (avgBackSuccess)
            + 0.50 * (avgBackFailure)
            - 0.80 * (success)
            - 0.20 * (failure)
        )

    success += succeedEffectFactor
    failure += failEffectFactor

    if (
        localState.surprise is None
        and len(currentDeck) > 1
        and isinstance(currentDeck[1], SurpriseCard)
    ):
        success += localState.priorities["obtain 3 loot"]

    return success, failure


def getAdjacentCards(challenge, localState=state):
    leftCard = rightCard = None
    if challenge.currentDeck == "villain":
        rightCard = localState.relicDeck[0]
    if challenge.currentDeck == "relic":
        leftCard = localState.villainDeck[0]
        rightCard = localState.locationDeck[0]
    if challenge.currentDeck == "location":
        leftCard = localState.relicDeck[0]
    return leftCard, rightCard


def getPriority(challenge, pc, helpers=None, lookAhead=True):
    # Returns overall outcome weighted by probabilities, success outcome, and failure outcome.
    # helpers can either be a PlayerCharacter (in which case, it means pre-roll assist),
    # an Ability (which means wizard/warrior ability), or
    # SurpriseCard / FkcCard (which means discard bonus.)
    localState = state
    if not lookAhead:
        localState = futureState
    if helpers is None:
        helpers = []
    # delta = 0
    # otherPCsBestDelta = 8
    # for player in localState.players:
    #     thisDelta = max(getDelta(challenge, player), 1)
    #     if player == pc:
    #         delta = thisDelta
    #     else:
    #         if thisDelta < otherPCsBestDelta:
    #             otherPCsBestDelta = thisDelta
    delta = getDelta(challenge, pc)
    # This is to better allocate players to challenges they specialize in
    # If they really are great at this challenge compared to everyone else,
    # the relativeProficiencyModifier is close to 2. If they're much worse
    # at it than someone else, the modifier is close to 0.5.
    # https://www.wolframalpha.com/input?i=plot+0.5+%2B+%281.5%29%2F%281%2B2%5E%282x%2B1%29%29%2C+x%3D-5..5
    # relativeProficiencyModifier = 0.5 + 1.5 / (
    #     1 + 2 ** (2 * (delta - otherPCsBestDelta) + 1)
    # )
    relativeProficiencyModifier = 1
    holdPriorityHelpers = 0
    for helper in helpers:
        delta -= helper.getAssistBefore(challenge.icons)
        holdPriorityHelpers += helper.getHoldPriority(localState=localState)
    if (
        "double assist" in challenge.icons
        and len(
            [
                True
                for player in localState.players
                if player.hasToken
                and (
                    "no assist"
                    not in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                )
                and (
                    player != pc
                    or "assist self"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                )
            ]
        )
        > 0
    ):
        delta -= 1
    # this is to treat loot 2 cards on the board as loot 1 if the player
    # already has a loot 2 card
    currentPlayerHasLoot2Card = pc.lootCards and pc.lootCards[0].loot == 2
    success, failure = getOutcomes(challenge, currentPlayerHasLoot2Card, localState)
    prob = getProbFromDelta(delta)

    leftCard, rightCard = getAdjacentCards(challenge, localState=localState)
    leftSuccess, leftFailure = getOutcomes(leftCard, localState=localState)
    rightSuccess, rightFailure = getOutcomes(rightCard, localState=localState)

    diffFactor = (
        state.priorities["next turn relevance factor"]
        * 0.15
        * (
            challenge.leftDiff * (leftSuccess - leftFailure)
            + challenge.rightDiff * (rightSuccess - rightFailure)
        )
    )

    if "win monster challenge" in [
        helper.discardEffect for helper in helpers if isinstance(helper, FKCCard)
    ]:
        return success + diffFactor - holdPriorityHelpers, success, failure
    if "any challenge 50%" in [
        helper.discardEffect for helper in helpers if isinstance(helper, FKCCard)
    ]:
        return (
            0.5 * success + 0.5 * failure + diffFactor - holdPriorityHelpers,
            success,
            failure,
        )
    ### testing
    # leftCardName = leftCard.name if leftCard is not None else "None"
    # rightCardName = rightCard.name if rightCard is not None else "None"
    # print(f">>>{challenge.name}: {success}, {failure}, {diffFactor}")
    # print(f">>>>{leftCardName}, {rightCardName}")
    ###

    return (
        prob * relativeProficiencyModifier * success
        + (1 - prob) * failure
        + diffFactor
        - holdPriorityHelpers,
        success,
        failure,
    )


def nextPlayer(localState=state):
    localState.currentPlayer += 1
    getPlayerCharacter("bard", localState).hasToken = True
    if localState.currentPlayer >= len(localState.players):
        localState.currentPlayer = 0
        for player in localState.players:
            player.hasToken = True


def getActiveCards():
    return [state.villainDeck[0], state.relicDeck[0], state.locationDeck[0]]


def getNumberOfAssistOpportunities(turnsRemaining=3):
    if turnsRemaining > 3:
        turnsRemaining = 3
    activeCards = getActiveCards()
    num = 0
    while turnsRemaining > 0:
        foundCard = False
        for card in activeCards:
            if "double assist" in card.icons:
                foundCard = True
                num += 2 + (1 if card.effect == "spend action token to engage" else 0)
                activeCards.remove(card)
                break
        if foundCard:
            turnsRemaining -= 1
            continue
        for card in activeCards:
            if "no assist" not in card.icons:
                num += 1 + (1 if card.effect == "spend action token to engage" else 0)
                activeCards.remove(card)
                break
        turnsRemaining -= 1

    return num


def getSurpriseOngoingPriority(any=False):
    fkcCardOngoing = (
        state.priorities["ongoing bonus any"]
        if any
        else state.priorities["ongoing bonus"]
    )

    numPlayers = len(state.players)
    return fkcCardOngoing * (1 + numPlayers * 0.2)


def assembleOptions(localState=state, currentDeckName=""):
    options = []
    activeCards = getActiveCards()
    lookAhead = localState == state

    for card in activeCards:
        if card.currentDeck == currentDeckName:
            activeCards.remove(card)
            break

    pc = localState.players[localState.currentPlayer]

    helpers = [
        player
        for player in localState.players
        if (
            player.hasToken
            and player.name not in ["priest", "bard"]
            and (
                "no assist"
                not in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
            and (
                player != pc
                or "assist self"
                in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
        )
    ]
    helpersAll = [
        player
        for player in localState.players
        if (
            player.name not in ["priest", "bard"]
            and (
                "no assist"
                not in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
            and (
                player != pc
                or "assist self"
                in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
        )
    ]
    strengthPotion = None
    for fkcCard in pc.fkcCards:
        if fkcCard.discardEffect == "+3 any die roll before":
            strengthPotion = fkcCard
    swordOfDoom = None
    for fkcCard in pc.fkcCards:
        if fkcCard.discardEffect == "win monster challenge":
            swordOfDoom = fkcCard
    ringOfRecall = None
    for fkcCard in pc.fkcCards:
        if fkcCard.discardEffect == "regain action tokens":
            ringOfRecall = fkcCard
    coin = None
    for fkcCard in pc.fkcCards:
        if fkcCard.discardEffect == "any challenge 50%":
            coin = fkcCard
    if (
        localState.surprise is not None
        and localState.surprise.discardEffect == "draw fkc card skip challenge"
    ):
        options.append(Option(localState.surprise, pc, lookAhead=lookAhead))
    for fkcCard in pc.fkcCards:
        if fkcCard.ongoingEffect == "recover 1 skip challenge":
            options.append(Option(fkcCard, pc, lookAhead=lookAhead))
    for card in activeCards:
        if not (
            card.effect == "spend action token to engage" and not pc.hasToken
        ) and not (card.finale and card.difficulty == 0):
            # consider the option of getting tokens back from Binicorn or Ring of Recall
            options.append(Option(card, pc, lookAhead=lookAhead))
            if "no assist" not in card.icons:
                for helper in helpers:
                    options.append(
                        Option(card, pc, helpers=[helper], lookAhead=lookAhead)
                    )
            if (
                (
                    pc.name == "wizard"
                    or (
                        "can use other players abilities"
                        in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
                        and "wizard" in [pc.name for pc in localState.players]
                    )
                )
                and "monster" in card.icons
                and pc.hasToken
            ):
                options.append(
                    Option(
                        card,
                        pc,
                        helpers=[Ability("wizard ability", pc)],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in helpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                helpers=[Ability("wizard ability", pc), helper],
                                lookAhead=lookAhead,
                            )
                        )
            if (
                pc.name == "warrior"
                or (
                    "can use other players abilities"
                    in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
                    and "warrior" in [pc.name for pc in localState.players]
                )
            ) and pc.hasToken:
                options.append(
                    Option(
                        card,
                        pc,
                        helpers=[Ability("warrior ability", pc)],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in helpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                helpers=[Ability("warrior ability", pc), helper],
                                lookAhead=lookAhead,
                            )
                        )

            if strengthPotion is not None:
                options.append(
                    Option(card, pc, helpers=[strengthPotion], lookAhead=lookAhead)
                )
                if "no assist" not in card.icons:
                    for helper in helpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                helpers=[strengthPotion, helper],
                                lookAhead=lookAhead,
                            )
                        )
            if coin is not None:
                options.append(Option(card, pc, helpers=[coin], lookAhead=lookAhead))

            if swordOfDoom is not None and "monster" in card.icons:
                options.append(
                    Option(card, pc, helpers=[swordOfDoom], lookAhead=lookAhead)
                )
            if ringOfRecall is not None and "no assist" not in card.icons:
                for helper in helpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            helpers=[ringOfRecall, helper],
                            lookAhead=lookAhead,
                        )
                    )
            if (
                localState.surprise is not None
                and localState.surprise.discardEffect == "regain action tokens"
                and "no assist" not in card.icons
            ):

                for helper in helpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            helpers=[localState.surprise, helper],
                            lookAhead=lookAhead,
                        )
                    )
        if (card.effect == "spend action token to engage" and not pc.hasToken) and not (
            card.finale and card.difficulty == 0
        ):
            if (
                localState.surprise is not None
                and localState.surprise.discardEffect == "regain action tokens"
            ):
                options.append(
                    Option(card, pc, helpers=[localState.surprise], lookAhead=lookAhead)
                )
                for helper in helpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            helpers=[localState.surprise, helper],
                            lookAhead=lookAhead,
                        )
                    )
            if ringOfRecall is not None:
                options.append(
                    Option(card, pc, helpers=[ringOfRecall], lookAhead=lookAhead)
                )
                for helper in helpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            helpers=[ringOfRecall, helper],
                            lookAhead=lookAhead,
                        )
                    )
    options = sorted(options, reverse=True)
    if not options:
        if state.display:
            print("No options possible! Skipping turn.")
        options.append(Option(None, pc))
    return options


def getCardClearPriority(decktype, localState=state, addToDeck=0):
    c1a = state.priorities["clear 1 card a"]
    c1b = state.priorities["clear 1 card b"]

    # villain deck length, relic deck length, location deck length
    vdl = len(localState.villainDeck)
    rdl = len(localState.relicDeck)
    ldl = len(localState.locationDeck)

    def inverseWithC1B(vdl, rdl, ldl):
        return 1 / (rdl + min(vdl, ldl) + c1b)

    if decktype == "villain":
        startingValue = inverseWithC1B(vdl + addToDeck, rdl, ldl)
        return c1a * (inverseWithC1B(vdl - 1 + addToDeck, rdl, ldl) - startingValue)
    if decktype == "relic":
        startingValue = inverseWithC1B(vdl, rdl + addToDeck, ldl)
        return c1a * (inverseWithC1B(vdl, rdl - 1 + addToDeck, ldl) - startingValue)
    if decktype == "location":
        startingValue = inverseWithC1B(vdl, rdl, ldl + addToDeck)
        return c1a * (inverseWithC1B(vdl, rdl, ldl - 1 + addToDeck) - startingValue)
    return None


def getHealthChangePriority(oldHealth, newHealth):
    hca = state.priorities["health change a"]
    hcb = state.priorities["health change b"]
    healthChangePriority = hca * (1 / (oldHealth + hcb) - 1 / (newHealth + hcb))
    return healthChangePriority


def getRecoverPriority(recoveryAmt, localState=state):
    newHealth = min(localState.health + recoveryAmt, localState.maxHealth)
    return getHealthChangePriority(localState.health, newHealth)


def getDamagePriority(dmgAmt, localState=state):
    newHealth = max(localState.health - dmgAmt, 0)
    return getHealthChangePriority(localState.health, newHealth)


def copyState():
    futureState.villain = state.villain
    futureState.relic = state.relic
    futureState.location = state.location
    futureState.won = state.won
    futureState.health = state.health
    futureState.maxHealth = state.maxHealth
    futureState.currentPlayer = state.currentPlayer
    futureState.relicTokens = state.relicTokens
    futureState.pendingDamage = state.pendingDamage
    futureState.villainDeck = copy.deepcopy(state.villainDeck)
    futureState.relicDeck = copy.deepcopy(state.relicDeck)
    futureState.locationDeck = copy.deepcopy(state.locationDeck)
    futureState.surpriseDeck = copy.deepcopy(state.surpriseDeck)
    futureState.fkcDeck = copy.deepcopy(state.fkcDeck)
    futureState.challengeDiscard = copy.deepcopy(state.challengeDiscard)
    futureState.surpriseDiscard = copy.deepcopy(state.surpriseDiscard)
    futureState.fkcDiscard = copy.deepcopy(state.fkcDiscard)
    futureState.surprise = copy.deepcopy(state.surprise)
    futureState.players = copy.deepcopy(state.players)
    futureState.priorities = copy.deepcopy(state.priorities)
