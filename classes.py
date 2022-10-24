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
        if (
            "spend token" in newFkcCard.ongoingEffect
            or "+1 assist any challenge" == newFkcCard.ongoingEffect
        ) and self.name != "bard":
            bardPlayer = getPlayerCharacter("bard")
            if bardPlayer is not None:
                if (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in bardPlayer.fkcCards]
                    or len(bardPlayer.fkcCards) < 2
                ):
                    bardPlayer.addFkcCard(newFkcCard)
                    return
        # don't give glutton's fork to the priest.
        # Could also make a consideration for wand of switcheroo but it makes
        # an annoying recursion loop
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
                newFkcCard.useDiscardAbility()
                return
        if (
            "regain action tokens" == newFkcCard.discardEffect
            and self.name == state.players[0].name
        ):
            # this card isn't useful on the first player's turn; try to give it to
            # pcs later in the round. Highest "regainTokenPriority" tends to be on
            # player 2. (or 1, if 0-indexed)

            for i in range(state.currentPlayer + 1, len(state.players)):
                player = state.players[i]
                if (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                    or len(player.fkcCards) < 2
                ):
                    player.addFkcCard(newFkcCard)
                    return
            # if no one else could take it, first player can try to take it
            if (
                "no fkc card limit"
                in [fkcCard.ongoingEffect for fkcCard in self.fkcCards]
                or "no fkc card limit" == newFkcCard.ongoingEffect
                or len(self.fkcCards) < 2
            ):
                newFkcCard.pc = self
                self.fkcCards.append(newFkcCard)
            else:
                # if not possible, discard least valuable and/or best discard effect
                newFkcCard.pc = self
                self.fkcCards.append(newFkcCard)
                mostDiscardable = newFkcCard
                for fkcCard in self.fkcCards:
                    if (
                        fkcCard.discardPriorityEOT()
                        > mostDiscardable.discardPriorityEOT()
                    ):
                        mostDiscardable = fkcCard
                mostDiscardable.useDiscardAbility()
            return

        if (
            "no fkc card limit" in [fkcCard.ongoingEffect for fkcCard in self.fkcCards]
            or "no fkc card limit" == newFkcCard.ongoingEffect
            or len(self.fkcCards) < 2
        ):
            newFkcCard.pc = self
            self.fkcCards.append(newFkcCard)
        else:
            # try to give the card to someone else;
            # prioritize players who haven't gone yet
            for i in range(state.currentPlayer + 1, len(state.players)):
                player = state.players[i]
                if (
                    "no fkc card limit"
                    in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                    or len(player.fkcCards) < 2
                ):
                    player.addFkcCard(newFkcCard)
                    return
            for i in range(0, state.currentPlayer):
                player = state.players[i]
                if (
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
            mostDiscardable.useDiscardAbility()

    def drawFkcCard(self):
        fkcCard = state.fkcDeck.pop()
        if self.name == "rogue":
            fkcCard2 = state.fkcDeck.pop()
            if fkcCard.getHoldPriority(
                skipDiscardEffect=True
            ) > fkcCard2.getHoldPriority(skipDiscardEffect=True):
                self.addFkcCard(fkcCard)
                fkcCard2.discard()
            else:
                self.addFkcCard(fkcCard2)
                fkcCard.discard()
        else:
            self.addFkcCard(fkcCard)

    def addLootCard(self, newLootCard):
        if newLootCard.loot == 0:
            state.challengeDiscard.append(newLootCard)
            return
        activeChallengeCards = getActiveCards()
        fkcCardsCost2 = "fkc cards cost 2" in [
            card.effect for card in activeChallengeCards
        ]

        if not fkcCardsCost2:
            if newLootCard.loot > 3:
                if (
                    self.lootCards
                    and sum([card.loot for card in self.lootCards]) + newLootCard.loot
                    >= 6
                ):
                    state.challengeDiscard.append(newLootCard)
                    while self.lootCards:
                        state.challengeDiscard.append(self.lootCards.pop())
                    self.drawFkcCard()
                    self.drawFkcCard()
                else:
                    state.challengeDiscard.append(newLootCard)
                    self.drawFkcCard()
            elif newLootCard.loot == 3:
                state.challengeDiscard.append(newLootCard)
                self.drawFkcCard()
            elif newLootCard.loot == 2:
                otherCard = None
                for lootCard in self.lootCards:
                    if lootCard.loot == 2:
                        otherCard = lootCard
                        break
                for lootCard in self.lootCards:
                    if lootCard.loot == 1:
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
        else:
            if newLootCard.loot > 3:
                state.challengeDiscard.append(newLootCard)
                self.drawFkcCard()
                self.drawFkcCard()
            elif newLootCard.loot in [3, 2]:
                state.challengeDiscard.append(newLootCard)
                self.drawFkcCard()
            elif newLootCard.loot == 1:
                if self.lootCards:
                    state.challengeDiscard.append(newLootCard)
                    state.challengeDiscard.append(self.lootCards.pop())
                    self.drawFkcCard()
                else:
                    self.lootCards.append(newLootCard)

    def getHoldTokenPriority(self, localState=state):
        # Priority for a given player to hold their token
        # if not self.hasToken:
        #     return 100
        if self.name == "bard":
            return -0.0001  # just so bard shows up first in priority

        playerNumber = 0
        for index, player in enumerate(localState.players):
            if player == self:
                playerNumber = index
                break

        holdPriority = 0

        turnsRemaining = len(localState.players) - 1 - localState.currentPlayer
        assistOpportunities = getNumberOfAssistOpportunities(turnsRemaining, localState)
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
            if self.name == "wizard":
                n += 1
            if self.name == "warrior":
                n += 0.5  # warrior's ability not as valuable
            for fkcCard in self.fkcCards:
                if "spend token" in fkcCard.ongoingEffect:
                    n += 1

            # holdPriority bonus = 1 when n = 1, approaches 2 as n increases
            # this is to indicate the value of saving your token until your turn
            holdPriority += (2 ** (1 - n)) * ((2**n) - 1)
            if self.name == "priest":
                holdPriority += getRecoverPriority(1)

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
        failAnyEffect=None,
        number=0,
        storyBonus=0,
        defeatCounters=0,
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
        self.failAnyEffect = failAnyEffect  # triggered by any failure
        self.reverse = reverse  # another ChallengeCard object
        self.number = number  # deck order number if relevant, or front/back
        self.storyBonus = storyBonus  # +1 if you add some story
        self.defeatCounters = defeatCounters  # crew / tomb have these
        self.currentDefeatCounters = defeatCounters
        self.finale = finale
        # currentDeck can change over course of game (e.g. Dark Lord)
        self.currentDeck = decktype

    def reveal(self, localState=state):
        if "chance" in self.icons:
            self.diffMod += random.choice(range(1, 7))
        if self.effect == "difficulty up 1 per relicCounter":
            self.diffMod += localState.relicCounters
        if self.defeatCounters > 0:
            self.currentDefeatCounters = self.defeatCounters
        if self.effect == "discard surprise on reveal":
            if localState.surprise is not None:
                localState.surprise.discard()
        if self.effect == "on reveal current player discards 1 loot":
            currentPlayer = localState.players[localState.currentPlayer]
            if currentPlayer.lootCards:
                localState.challengeDiscard.append(currentPlayer.lootCards.pop())
        if self.effect == "fkc cards cost 2":
            for player in localState.players:
                if (
                    player.lootCards
                    and sum([card.loot for card in player.lootCards]) >= 2
                ):
                    if state.display:
                        print(
                            f"The {player.name} is trading in loot cards for an FKC card."
                        )
                    while player.lootCards:
                        localState.challengeDiscard.append(player.lootCards.pop())
                    player.drawFkcCard()
        if self.effect == "lose on reveal":
            localState.won = False

    def getDifficulty(self):
        difficulty = (
            self.difficulty
            + self.diffMod
            + cardBoost(self.decktype, "left")
            + cardBoost(self.decktype, "right")
        )
        activeChallengeCards = getActiveCards()
        effects = [card.effect for card in activeChallengeCards if card != self]
        if "spooky or magic challenges -1 difficulty" in effects and (
            "spooky" in self.icons or "magic" in self.icons
        ):
            difficulty -= 1
        if "monster or trap challenges +1 difficulty" in effects and (
            "monster" in self.icons or "trap" in self.icons
        ):
            difficulty += 1
        if "spooky or magic challenges +1 difficulty" in effects and (
            "spooky" in self.icons or "magic" in self.icons
        ):
            difficulty += 1
        if "spooky challenges -1 difficulty" in effects and "spooky" in self.icons:
            difficulty -= 1
        if "spooky challenges +1 difficulty" in effects and "spooky" in self.icons:
            difficulty += 1
        if "trap challenges +1 difficulty" in effects and "trap" in self.icons:
            difficulty += 1
        if "monster challenges +1 difficulty" in effects and "monster" in self.icons:
            difficulty += 1
        if "magic challenges +1 difficulty" in effects and "magic" in self.icons:
            difficulty += 1
        if "all challenges +1 difficulty" in effects:
            difficulty += 1
        if "monster challenges -2 difficulty" in effects and "monster" in self.icons:
            difficulty -= 2
        return difficulty

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
        self.decktype = ""
        self.failAnyEffect = ""
        self.finale = False
        self.icons = []

    def reveal(self):
        currentDeck = getDeckFromType(self.currentDeck)
        currentDeck.remove(self)
        if state.surprise is None:
            state.surprise = self
        else:
            if self.discardPriorityEOT() > state.surprise.discardPriorityEOT():
                self.useDiscardAbility()
            else:
                state.surprise.useDiscardAbility()
                state.surprise = self
        currentDeck[0].reveal()

    def discardPriorityEOT(self):
        recoverPriority = getRecoverPriority(3)
        # Should be 3.8 if healing from 7 to 10; 2.2 if healing from 8 to 10; 1.0 if healing from 9 to 10

        flipPriority = 0
        activeCards = getActiveCards()
        for card in activeCards:
            # TODO: consider also flipping if none of the current challenge cards are strong vs
            if card.deck in ["cult", "idol"] and card.number == 2:
                flipPriority += 1
            if card.effect == "can discard loot to flip":
                flipPriority += 1.5
            if card.effect == "move down 2, relicCounters up 1":
                flipPriority += len(state.relicDeck) / 2
            if "chance" in card.icons and card.diffMod > 4:
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
            holdPriority = 0
        if self.discardEffect == "+2 any die roll suffer 1 damage":
            holdPriority -= getDamagePriority(1)
        return holdPriority

    def useDiscardAbility(self):
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
            # todo: include other flippable cards
            activeCards = getActiveCards()
            for card in activeCards:
                if (
                    (card.deck in ["cult", "idol"] and card.number == 2)
                    or (card.effect == "can discard loot to flip")
                    or (card.effect == "move down 2, relicCounters up 1")
                    or ("chance" in card.icons and card.diffMod > 4)
                ) and not card.finale:
                    card = card.reverse
        if self.discardEffect == "+2 any die roll suffer 1 damage":
            state.health -= 1
            if state.health < 1:
                state.won = False

        self.discard()

    def discard(self):
        if self == state.surprise:
            state.surprise = None
        state.surpriseDiscard.append(self)

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
        # Should be 3.8 if healing from 7 to 10; 2.2 if healing from 8 to 10; 1.0 if healing from 9 to 10
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

    def getHoldPriority(
        self, currentDeck=None, localState=state, skipDiscardEffect=False
    ):
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

        if skipDiscardEffect:
            discardEffectValue += {
                "recover 3": getRecoverPriority(3),
                "recover 2": getRecoverPriority(2),
            }.get(self.discardEffect, 0)

        holdPriority += discardEffectValue
        return holdPriority

    def useDiscardAbility(self):
        if self.discardEffect == "regain action tokens":
            for player in state.players:
                player.hasToken = True
        if self.discardEffect == "recover 3":
            state.health = min(state.health + 3, state.maxHealth)
        if self.discardEffect == "recover 2":
            state.health = min(state.health + 2, state.maxHealth)
        if self.discardEffect == "no damage after fail any player":
            state.pendingDamage = 0

        self.discard()

    def discard(self):
        if self.pc is not None:
            self.pc.fkcCards.remove(self)
        self.pc = None
        state.fkcDiscard.append(self)

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
    def __init__(self, card, pc, allOutcomes=None, helpers=None, lookAhead=True):
        self.pc = pc
        self.name = card.name if card is not None else ""
        self.card = card  # either a challenge card or a choice to skip a challenge
        if helpers is None:
            helpers = []
        self.helpers = helpers
        self.priority = 0
        self.success = 0
        self.failure = 0
        self.assists = 0
        if isinstance(card, ChallengeCard):
            self.priority, self.success, self.failure = getPriority(
                card, pc, allOutcomes, helpers, lookAhead
            )
            # nextPlayer = state.currentPlayer + 1
            # if nextPlayer >= len(state.players):
            #     nextPlayer = 0
            if (
                lookAhead
                # and not oneDeckClear()
                # and state.location not in ["train", "race"]
            ):  # look ahead one turn
                # adjudicate the action, assume success,
                # update things in futureState, then generate Options (minus this one)
                # and get the greatest priority of the next player.
                # Add that to this priority.
                # Don't consider the added options from current player if
                # villain is Crew; it's too much.
                copyState()
                currentDeckFutureState = getDeckFromType(
                    self.card.currentDeck, futureState
                )
                currentDeckType = self.card.currentDeck
                if self.card.currentDefeatCounters > 0:
                    currentDeckType = ""
                self.handleSuccessFutureState(currentDeckFutureState)
                if not futureState.won:
                    futureOptions = assembleOptions(
                        localState=futureState, currentDeckType=currentDeckType
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
            # if a challenge card is a "tribute" type card, where you can give up
            # an fkc card to automatically succeed, it takes the form of:
            # self.card = the fkc card to be discarded, and
            # helpers[0] = the challenge card.
            if (
                isinstance(card, FKCCard)
                and helpers
                and isinstance(helpers[0], ChallengeCard)
                and helpers[0].effect == "can discard fkc card to succeed"
            ):
                # priority = success
                _, self.priority, _ = getPriority(
                    helpers[0], pc, allOutcomes, None, lookAhead
                )
                self.priority -= card.getHoldPriority(skipDiscardEffect=True)
                if (
                    lookAhead
                    # and not oneDeckClear()
                    # and state.location not in ["train", "race"]
                ):
                    copyState()
                    currentDeck = getDeckFromType(helpers[0].currentDeck)
                    self.handleEndOfTurn(futureState)
                    if not futureState.won:
                        futureOptions = assembleOptions(
                            localState=futureState,
                            currentDeckType=helpers[0].currentDeck,
                        )
                        if futureOptions:
                            self.priority += (
                                state.priorities["next turn relevance factor"]
                                * futureOptions[0].priority
                            )

    # sort by priority. Unless success is a negative number, then always put those
    # options at the bottom.
    def __eq__(self, obj):
        return (
            self.success >= 0 and obj.success >= 0 and self.priority == obj.priority
        ) or (self.success < 0 and obj.success < 0 and self.priority == obj.priority)

    def __lt__(self, obj):
        return (
            (self.success >= 0 and obj.success >= 0 and self.priority < obj.priority)
            or (self.success < 0 and obj.success < 0 and self.priority < obj.priority)
            or (self.success < 0 and obj.success >= 0)
        )

    def __gt__(self, obj):
        return (
            (self.success >= 0 and obj.success >= 0 and self.priority > obj.priority)
            or (self.success < 0 and obj.success < 0 and self.priority > obj.priority)
            or (self.success >= 0 and obj.success < 0)
        )

    def __le__(self, obj):
        return (
            (self.success >= 0 and obj.success >= 0 and self.priority <= obj.priority)
            or (self.success < 0 and obj.success < 0 and self.priority <= obj.priority)
            or (self.success < 0 and obj.success >= 0)
        )

    def __ge__(self, obj):
        return (
            (self.success >= 0 and obj.success >= 0 and self.priority >= obj.priority)
            or (self.success < 0 and obj.success < 0 and self.priority >= obj.priority)
            or (self.success >= 0 and obj.success < 0)
        )

    def handleSuccess(self, currentDeck):
        # Todo: add the rest
        if state.display:
            print("\033[92mSuccess!\033[0m\n")
        if self.card.finale:
            self.pc.drawFkcCard()
        if self.card.succeedEffect == "flip self" or self.card.finale:
            if self.card.currentDefeatCounters == 0:
                self.card.diffMod = 0
                self.card.damageMod = 0
                currentDeck[0] = currentDeck[0].reverse
            else:
                self.card.currentDefeatCounters -= 1
                self.handleEndOfTurn(clearedChallenge=self.card.deck)
                return
        elif self.card.succeedEffect == "move down 2, relicCounters up 1":
            currentDeck.remove(self.card)
            currentDeck.insert(2, self.card)
            state.relicCounters += 1
        else:
            if self.card.currentDefeatCounters == 0:
                returnedCard = None
                if self.card.succeedEffect == "return top discarded challenge":
                    # gotta do this before adding loot card, since that might
                    # trigger a fkc card purchase which changes the discard pile
                    if state.challengeDiscard:
                        returnedCard = state.challengeDiscard.pop()
                        returnedDeck = getDeckFromType(returnedCard.decktype)
                        returnedDeck.insert(0, returnedCard)
                        returnedCard.reveal()
                self.card.diffMod = 0
                self.card.damageMod = 0
                currentDeck.remove(self.card)
                self.pc.addLootCard(self.card)
                if (
                    returnedCard is not None
                    and returnedCard.decktype == self.card.currentDeck
                ):
                    # don't reveal the same card twice
                    self.handleEndOfTurn(clearedChallenge=self.card.deck)
                    return
            else:
                self.card.currentDefeatCounters -= 1
                self.handleEndOfTurn(clearedChallenge=self.card.deck)
                return
        if self.card.succeedEffect == "flip next":
            if not currentDeck[0].finale:
                currentDeck[0] = currentDeck[0].reverse
        if self.card.succeedEffect == "flip next recover 1":
            if not currentDeck[0].finale:
                currentDeck[0] = currentDeck[0].reverse
            state.health = min(state.health + 1, state.maxHealth)
        if self.card.succeedEffect == "recover 2":
            state.health = min(state.health + 2, state.maxHealth)
        if self.card.succeedEffect == "recover 3":
            state.health = min(state.health + 3, state.maxHealth)
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
        currentDeck[0].reveal()  # whether new card or flipped
        self.handleEndOfTurn(clearedChallenge=self.card.deck)

    def handleSuccessFutureState(self, currentDeck):
        for helper in self.helpers:
            if isinstance(helper, PlayerCharacter):
                getPlayerCharacter(helper.name, futureState).hasToken = False
            elif isinstance(helper, Ability):
                if helper.name == "wizard ability" and "monster" in self.card.icons:
                    getPlayerCharacter(self.pc.name, futureState).hasToken = False
                if helper.name == "warrior ability":
                    futureState.health -= 1
                    if futureState.health < 1:
                        futureState.won = False
                        return
                    getPlayerCharacter(self.pc.name, futureState).hasToken = False
            elif isinstance(helper, SurpriseCard):
                futureState.surprise = None
            elif isinstance(helper, SpecialHelper):
                if helper.name == "sacrifice health":
                    futureState.health -= helper.quantity
                    if futureState.health < 1:
                        futureState.won = False
                        return
            else:
                futurePC = getPlayerCharacter(self.pc.name, futureState)
                for fkcCard in futurePC.fkcCards:
                    if fkcCard.discardEffect == helper.discardEffect:
                        futurePC.fkcCards.remove(fkcCard)

        if (
            self.card.succeedEffect != "flip self"
            and self.card.currentDefeatCounters == 0
            and not self.card.finale
        ):
            currentDeck.pop(0)

        if self.card.succeedEffect == "flip next recover 1":
            futureState.health = min(futureState.health + 1, futureState.maxHealth)
        if self.card.succeedEffect == "recover 2":
            futureState.health = min(futureState.health + 2, futureState.maxHealth)
        if self.card.succeedEffect == "recover 3":
            futureState.health = min(futureState.health + 3, futureState.maxHealth)
        if self.card.succeedEffect == "flip villain":
            if not futureState.villainDeck[0].finale:
                futureState.villainDeck[0] = futureState.villainDeck[0].reverse
                futureState.villainDeck[0].reveal(futureState)
        if self.card.succeedEffect == "flip relic":
            if not futureState.relicDeck[0].finale:
                futureState.relicDeck[0] = futureState.relicDeck[0].reverse
                futureState.relicDeck[0].reveal(futureState)
        if self.card.succeedEffect == "flip location":
            if not futureState.locationDeck[0].finale:
                futureState.locationDeck[0] = futureState.locationDeck[0].reverse
                futureState.locationDeck[0].reveal(futureState)
        if self.card.succeedEffect == "return top discarded challenge":
            if futureState.challengeDiscard:
                returnedCard = futureState.challengeDiscard.pop()
                returnedDeck = getDeckFromType(returnedCard.decktype, futureState)
                returnedDeck.insert(0, returnedCard)
                returnedCard.reveal(futureState)
        self.handleEndOfTurn(futureState)

    def handleFailure(self, currentDeck):
        # TODO
        self.handleEndOfTurn()

    def handleEndOfTurn(self, localState=state, clearedChallenge=None):
        # Healing and other end-of-turn things
        # tokens first.
        # after that, consider end-of-turn discard effects
        if deckDefeated("relic") and (
            deckDefeated("location") or deckDefeated("villain")
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
                    fkcCard.useDiscardAbility()
        if (
            localState.surprise is not None
            and localState.surprise.discardPriorityEOT() > 0.5
        ):
            if localState == state and state.display:
                print(f"Discarding {localState.surprise.name}...")
            localState.surprise.useDiscardAbility()

        # restore tokens
        getPlayerCharacter("bard", localState).hasToken = True

        if (
            localState == state
            and state.villain == "crew"
            and clearedChallenge is not None
            and (clearedChallenge == "crew" or deckDefeated("villain"))
        ):
            # if the villain is crew, we need to determine whether we should
            # advance to the next player or stay with the current one.
            # This choice can occur when we clear a Crew challenge card,
            # or any challenge card once we've defeated the Crew.
            # No need to calculate best options for futureState;
            # lookAhead in option init accounts for this

            copyState()
            currentDeck = getDeckFromType(self.card.currentDeck)

            if not futureState.won:
                futureOptionsSelf = assembleOptions(localState=futureState)
                nextPlayer(futureState)
                futureOptionsNext = assembleOptions(localState=futureState)

                if futureOptionsSelf[0].priority < futureOptionsNext[0].priority:
                    nextPlayer(localState)
                elif state.display:
                    print("Choosing not to advance to the next player.")
        else:
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
                        helper.useDiscardAbility()
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

            # end-of-turn effects for cards we didn't choose (this needs to happen
            # before handleSuccess etc)
            activeCards = getActiveCards()
            activeCards.remove(self.card)
            for card in activeCards:
                if card.effect == "flip at end of turn":
                    currentDeck = getDeckFromType(card.currentDeck)
                    currentDeck[0] = currentDeck[0].reverse

            currentDeck = getDeckFromType(self.card.currentDeck)
            if (
                self.card.effect == "can discard loot to flip"
                and len(self.pc.lootCards) == 2
                # if pc has two 1-loot cards, it's always worth it to make
                # mercenary easier and get 2 more loot
            ):
                state.challengeDiscard.append(self.pc.lootCards.pop())
                currentDeck[0] = currentDeck[0].reverse
                self.card = currentDeck[0]
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
                        if state.health < 1:
                            state.won = False
                            return
                        self.pc.hasToken = False
                elif isinstance(helper, SpecialHelper):
                    if helper.name == "sacrifice health":
                        helperBonus += helper.quantity
                        state.health -= helper.quantity
                        if state.health < 1:
                            state.won = False
                            return
                else:
                    # Other helpers are FKC or Surprise cards to be discarded.
                    if (
                        helper.discardEffect == "win monster challenge"
                        and "monster" in self.card.icons
                    ):
                        helper.useDiscardAbility()
                        self.handleSuccess(currentDeck)
                        return

                    if helper.discardEffect == "any challenge 50%":
                        useCoin = True

                    helperBonus += helper.getAssistBefore(self.card.icons)
                    # "assistAfter"s should only be used before the "roll" if "no dice"
                    # is in the challenge card's icons. Any fkc/surprise helpers
                    # that have getAssistAfter > 0 will only be added for "no dice" challenges

                    helperBonus += helper.getAssistAfter(self.card.icons)
                    helper.useDiscardAbility()

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

            if ("no dice" not in self.card.icons and diceroll < prob) or (
                "no dice" in self.card.icons and adjustedDelta < 1
            ):
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

                if "no dice" not in self.card.icons and not useCoin:
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
                            scoundrelsDice.useDiscardAbility()
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
                        safetyHarness.useDiscardAbility()
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
                            phantomFist.useDiscardAbility()
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
                        self.card.failEffect
                        in ["succeed after damage", "discard after damage"]
                        and len(currentDeck) > 1
                        and isinstance(currentDeck[1], SurpriseCard)
                    ):
                        # if we're about to unveil another surprise card anyway
                        noDiscardPriority = 0
                    if discardPriority > noDiscardPriority:
                        state.surprise.useDiscardAbility()

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
                if self.card.failEffect == "damage up 1":
                    self.card.damageMod += 1
                if self.card.failEffect == "discard all loot":
                    while self.pc.lootCards:
                        state.challengeDiscard.append(self.pc.lootCards.pop())
                if self.card.failEffect == "discard 1 loot":
                    if self.pc.lootCards:
                        state.challengeDiscard.append(self.pc.lootCards.pop())
                if self.card.failEffect == "all players discard action tokens":
                    for player in state.players:
                        player.hasToken = False
                if self.card.failEffect == "succeed after damage":
                    currentDeck.remove(self.card)
                    self.pc.lootCards.append(self.card)
                    self.card.diffMod = 0
                    self.card.damageMod = 0
                    currentDeck[0].reveal()
                if self.card.failEffect == "discard after damage":
                    currentDeck.remove(self.card)
                    state.challengeDiscard.append(self.card)
                    self.card.diffMod = 0
                    self.card.damageMod = 0
                    currentDeck[0].reveal()
                if self.card.failEffect == "return gerblin":
                    # currentDeck.remove(self.card)
                    # state.challengeDiscard.append(self.card)
                    self.card.diffMod = 0
                    self.card.damageMod = 0
                    gerblinCard = None
                    for card in state.challengeDiscard:
                        if "gerblin" in card.name.lower():
                            gerblinCard = card
                            break
                    if gerblinCard is not None:
                        state.challengeDiscard.remove(gerblinCard)
                        gerblinCard.currentDeck = "villain"
                        state.villainDeck.insert(0, gerblinCard)

                    currentDeck[0].reveal()

                # failAnyEffects, trigger on any failure
                for card in getActiveCards():
                    if card.failAnyEffect == "damage up 1":
                        card.damageMod += 1
                    if card.failAnyEffect == "discard self":
                        state.locationDeck.remove(card)
                        state.challengeDiscard.append(card)
                        card.diffMod = 0
                        card.damageMod = 0
                        state.locationDeck[0].reveal()

                self.handleEndOfTurn()
        else:
            # Not a challenge card
            if (
                isinstance(self.card, FKCCard)
                and self.helpers
                and isinstance(self.helpers[0], ChallengeCard)
                and self.helpers[0].effect == "can discard fkc card to succeed"
            ):
                self.card.discard()
                self.card = self.helpers.pop()
                currentDeck = getDeckFromType(self.card.currentDeck)
                self.handleSuccess(currentDeck)
            elif self.card.discardEffect == "draw fkc card skip challenge":
                self.pc.drawFkcCard()
                self.card.useDiscardAbility()
                self.handleEndOfTurn()
            elif self.card.ongoingEffect == "recover 1 skip challenge":
                state.health = min(state.health + 1, state.maxHealth)
                self.handleEndOfTurn()


class Ability:
    def __init__(self, name, pc):
        self.name = name
        self.pc = pc

    def getAssistBefore(self, icons):
        if self.name == "wizard ability" and "monster" in icons:
            return 3
        if self.name == "warrior ability":
            return 2
        return 0

    def getAssistAfter(self, icons):
        return 0

    def getHoldPriority(self, currentDeck=None, localState=state):
        holdPriority = self.pc.getHoldPriority()
        if self.name == "warrior ability":
            holdPriority += getHealthChangePriority(
                max(localState.health - 1, 0), localState.health
            )
        return holdPriority


class SpecialHelper:
    def __init__(self, name, quantity):
        self.name = name
        self.quantity = quantity

    def getAssistBefore(self, icons):
        if self.name == "sacrifice health":
            return self.quantity
        return 0

    def getAssistAfter(self, icons):
        return 0

    def getHoldPriority(self, currentDeck=None, localState=state):
        holdPriority = 0
        if self.name == "sacrifice health":
            holdPriority += getHealthChangePriority(
                max(localState.health - self.quantity, 0), localState.health
            )
        return holdPriority


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


def deckDefeated(decktype, localState=state):
    if (
        decktype == "villain"
        and localState.villainDeck[0].finale
        and localState.villainDeck[0].difficulty == 0
    ):
        return True
    if (
        decktype == "relic"
        and localState.relicDeck[0].finale
        and localState.relicDeck[0].difficulty == 0
    ):
        return True
    if (
        decktype == "location"
        and localState.locationDeck[0].finale
        and localState.locationDeck[0].difficulty == 0
        and localState.location not in ["train", "race"]
    ):
        return True
    return False


def oneDeckClear(localState=state):
    if deckDefeated("villain", localState):
        return "villain"
    if deckDefeated("relic", localState):
        return "relic"
    if deckDefeated("location", localState):
        return "location"

    return False


def calculateOutcomes(
    challenge,
    currentPlayerLoot=None,
    currentPlayerFKCCards=None,
    localState=state,
):
    if currentPlayerLoot == None:
        currentPlayerLoot = []
    if currentPlayerFKCCards == None:
        currentPlayerFKCCards = []
    if (
        challenge is None
        or isinstance(challenge, SurpriseCard)
        or (challenge.finale and challenge.difficulty == 0)
    ):
        return 0, 0

    ntrf = localState.priorities["next turn relevance factor"]

    currentDeck = getDeckFromType(challenge.currentDeck)

    # this is to treat loot 2 cards on the board as loot 1 if the player
    # already has a loot 2 card
    currentPlayerHas2Loot = (
        currentPlayerLoot and sum([card.loot for card in currentPlayerLoot]) == 2
    )
    # might consider using priorities.yaml for loot priority
    # todo: hoard done effect
    success = challenge.loot + getCardClearPriority(challenge.currentDeck, localState)
    if currentPlayerHas2Loot and challenge.loot == 2:
        success = 1 + getCardClearPriority(challenge.currentDeck, localState)
    if not currentPlayerHas2Loot and challenge.loot == 4:
        success = 3 + getCardClearPriority(challenge.currentDeck, localState)
    failure = getDamagePriority(challenge.getDamage(), localState)
    dmgAmt = challenge.getDamage()
    if "after fail reduce damage by 1" in [
        fkcCard.ongoingEffect for fkcCard in currentPlayerFKCCards
    ]:
        dmgAmt = max(challenge.getDamage() - 1, 0)
        failure = getDamagePriority(dmgAmt, localState)

    slippies = None
    for fkcCard in currentPlayerFKCCards:
        if "after fail reduce damage by 1" == fkcCard.ongoingEffect:
            slippies = fkcCard
            break
    if slippies is not None and slippies.pc.hasToken:
        failure = min(
            failure,
            getDamagePriority(max(dmgAmt - 1, 0), localState)
            + slippies.pc.getHoldTokenPriority(),
        )
    shield = None
    for player in localState.players:
        for fkcCard in player.fkcCards:
            if (
                "spend token after fail reduce damage by 2 any player"
                == fkcCard.ongoingEffect
            ):
                shield = fkcCard
                break

    if shield is not None and shield.pc.hasToken:
        failure = min(
            failure,
            getDamagePriority(max(dmgAmt - 2, 0), localState)
            + shield.pc.getHoldTokenPriority(),
        )

    if "no damage after fail any player" in [
        fkcCard.ongoingEffect for fkcCard in currentPlayerFKCCards
    ]:
        failure = min(state.priorities["ongoing bonus"], failure)
    if "no damage after fail but discard this" in [
        fkcCard.ongoingEffect for fkcCard in currentPlayerFKCCards
    ]:
        failure = state.priorities["ongoing bonus any"]
    # todo: put all of these in priorities.yaml

    succeedEffectFactor = 0
    if challenge.succeedEffect == "return top discarded challenge":
        if localState.challengeDiscard:
            returnedCard = localState.challengeDiscard[-1]
            succeedEffectFactor = ntrf * getCardAddPriority(
                returnedCard.decktype, localState
            )
    if challenge.succeedEffect == "flip next recover 1":
        succeedEffectFactor = getRecoverPriority(1, localState)
    if challenge.succeedEffect == "recover 2":
        succeedEffectFactor = getRecoverPriority(2, localState)
    if challenge.succeedEffect == "recover 3":
        succeedEffectFactor = getRecoverPriority(3, localState)
    if challenge.succeedEffect == "flip relic":
        if localState.relicDeck[0].effect == "can discard loot to flip":
            succeedEffectFactor += 1.5
        if localState.relicDeck[0].effect == "move down 2, relicCounters up 1":
            succeedEffectFactor += len(localState.relicDeck) / 2

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
    if challenge.failEffect == "discard after damage":
        failEffectFactor = getCardClearPriority(challenge.currentDeck, localState)
    if challenge.failEffect == "damage up 2":
        futureFailure = getDamagePriority(challenge.getDamage() + 2, localState)
        failEffectFactor = ntrf * 0.5 * (futureFailure - failure)
    if challenge.failEffect == "damage up 1":
        futureFailure = getDamagePriority(challenge.getDamage() + 1, localState)
        failEffectFactor = ntrf * 0.5 * (futureFailure - failure)
    if challenge.failEffect == "discard all loot":
        failEffectFactor = -1 * sum([card.loot for card in currentPlayerLoot])
    if challenge.failEffect == "discard 1 loot" and currentPlayerLoot:
        failEffectFactor = -1 * min([card.loot for card in currentPlayerLoot])
    if challenge.failEffect == "flip self":
        # averaged cult/idol 2 cards, assumed 80% chance on front side
        # average 2 card is 2 points higher in difficulty (30% lower chance)
        # does 3 points of damage, and gives 1 more loot
        avgBackSuccess = (challenge.loot + 1) + getCardClearPriority(
            challenge.currentDeck, localState
        )
        avgBackFailure = getDamagePriority(3, localState)
        failEffectFactor = ntrf * (
            0.50 * (avgBackSuccess)
            + 0.50 * (avgBackFailure)
            - 0.80 * (success)
            - 0.20 * (failure)
        )
    if challenge.failEffect == "flip relic":
        if localState.relicDeck[0].effect == "can discard loot to flip":
            failEffectFactor += 1.5
        if localState.relicDeck[0].effect == "move down 2, relicCounters up 1":
            failEffectFactor += len(localState.relicDeck) / 2
    if challenge.failEffect == "return gerblin":
        gerblinInDiscard = any(
            "Gerblin" in card.name for card in localState.challengeDiscard
        )
        if gerblinInDiscard:
            failEffectFactor = ntrf * getCardAddPriority("villain", localState)

    for card in getActiveCards(localState):
        if card.failAnyEffect == "damage up 1":
            currentFailure = getDamagePriority(card.getDamage(), localState)
            futureFailure = getDamagePriority(card.getDamage() + 1, localState)
            failEffectFactor += ntrf * 0.5 * (futureFailure - currentFailure)
        if card.failAnyEffect == "discard self":
            failEffectFactor += getCardClearPriority(card.currentDeck, localState)

    success += succeedEffectFactor
    failure += failEffectFactor

    if (
        localState.surprise is None
        and len(currentDeck) > 1
        and isinstance(currentDeck[1], SurpriseCard)
        and challenge.deck not in ["train", "race"]
    ):
        # if we are about to reveal a surprise card and we don't currently
        # have one, that's worth about 1 fkc card
        success += localState.priorities["obtain 3 loot"]

    return success, failure


def getAllOutcomes(activeCards, lookAhead=True):
    localState = state
    if not lookAhead:
        localState = futureState
    pc = localState.players[localState.currentPlayer]

    allOutcomes = []
    for activeCard in activeCards:
        success, failure = calculateOutcomes(
            activeCard, pc.lootCards, pc.fkcCards, localState
        )
        allOutcomes.append({"card": activeCard, "success": success, "failure": failure})
    return allOutcomes


def getOutcomes(challenge, allOutcomes):
    success = 0
    failure = 0
    for outcome in allOutcomes:
        if outcome["card"] == challenge:
            success = outcome["success"]
            failure = outcome["failure"]
            break
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


def getPriority(challenge, pc, allOutcomes, helpers=None, lookAhead=True):
    # Returns overall outcome weighted by probabilities, success outcome, and failure outcome.
    # Helpers can either be a PlayerCharacter (in which case, it means pre-roll assist),
    # an Ability (which means wizard/warrior ability), or
    # SurpriseCard / FkcCard (which means discard bonus.)
    if isinstance(challenge, SurpriseCard):
        return 0, 0, 0
    localState = state
    if not lookAhead:
        localState = futureState
    if helpers is None:
        helpers = []
    delta = getDelta(challenge, pc)
    if challenge.effect == "can discard loot to flip" and len(pc.lootCards) == 2:
        delta = getDelta(challenge.reverse, pc)
    holdPriorityHelpers = 0
    assists = 0
    pcsSpendingTokens = []
    sacrificedHealth = 0
    playerHelper = None
    tokensRestored = False
    for helper in helpers:
        delta -= helper.getAssistBefore(challenge.icons)
        if isinstance(helper, FKCCard) or isinstance(helper, SurpriseCard):
            delta -= helper.getAssistAfter(challenge.icons)
            if helper.discardEffect == "regain action tokens":
                tokensRestored = True
                regainTokenPriority = 0
                turnsRemaining = len(localState.players) - 1 - localState.currentPlayer
                assistOpportunities = getNumberOfAssistOpportunities(
                    turnsRemaining, localState
                )
                assistTokensAvailable = len(
                    [True for player in localState.players if player.hasToken]
                )
                assistTokensExpended = len(localState.players) - assistTokensAvailable
                regainTokenPriority = 0.5 * min(
                    max(assistOpportunities - assistTokensAvailable, 0),
                    assistTokensExpended,
                )
                holdPriorityHelpers -= regainTokenPriority

        if isinstance(helper, PlayerCharacter):
            assists += 1
            pcsSpendingTokens.append(helper)
            playerHelper = helper
        if isinstance(helper, Ability):
            pcsSpendingTokens.append(helper.pc)
            if helper.name == "warrior ability":
                sacrificedHealth += 1
        if isinstance(helper, SpecialHelper):
            if helper.name == "sacrifice health":
                sacrificedHealth += helper.quantity
        if (
            not isinstance(helper, FKCCard)
            or challenge.loot + sum([card.loot for card in pc.lootCards]) < 3
            or len(pc.fkcCards) < 2
        ):
            holdPriorityHelpers += helper.getHoldPriority(localState=localState)
    # this next bit is assuming we will use an after-roll assist if one is available.
    # this assist will be worth 1 on average (2 if facing the Giant).
    if (
        ("double assist" in challenge.icons and assists < 2)
        or ("no assist" not in challenge.icons and assists < 1)
    ) and len(
        [
            True
            for player in localState.players
            if (player.hasToken or tokensRestored)
            and (
                "no assist"
                not in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
            and (
                player != pc
                or "assist self"
                in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
            )
            and player != playerHelper
        ]
    ) > 0:
        delta -= 1
        if state.villain == "giant":
            delta -= 1

    mightAsWellTryFactor = 0
    # sometimes, even with assists, we still need a critical to succeed. However,
    # if there's no reason to hold back on spending tokens, we might as well spend
    # them just to get a little closer; after-roll benefits might help us get there.
    # This small boost to priority should break ties with options that have no assist

    if (
        delta > 6
        and playerHelper is not None
        and playerHelper.getHoldPriority(localState=localState) == 0
    ):
        mightAsWellTryFactor = 0.001 * playerHelper.getAssistBefore(challenge.icons)

    success, failure = getOutcomes(challenge, allOutcomes)

    if sacrificedHealth > 0 and not any(
        effect in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
        for effect in [
            "no damage after fail but discard this",
            "no damage after fail any player",
        ]
    ):
        dmgAmt = challenge.getDamage()
        if "after fail reduce damage by 1" in [
            fkcCard.ongoingEffect for fkcCard in pc.fkcCards
        ]:
            dmgAmt = max(dmgAmt - 1, 0)
        newHealth = max(localState.health - dmgAmt - sacrificedHealth, 0)
        failure = getHealthChangePriority(
            localState.health - sacrificedHealth, newHealth
        )
    prob = getProbFromDelta(delta)

    if challenge.effect == "roll twice pick worst":
        prob = prob * prob
    if challenge.effect == "roll twice pick best":
        prob = 1 - ((1 - prob) * (1 - prob))

    leftCard, rightCard = getAdjacentCards(challenge, localState=localState)
    leftSuccess, leftFailure = getOutcomes(leftCard, allOutcomes)
    rightSuccess, rightFailure = getOutcomes(rightCard, allOutcomes)
    if (
        rightCard
        and isinstance(rightCard, ChallengeCard)
        and rightCard.deck in ["train", "race"]
    ):
        rightSuccess, rightFailure = 0, 0

    diffFactor = (
        state.priorities["next turn relevance factor"]
        * 0.15
        * (
            challenge.leftDiff * (leftSuccess - leftFailure)
            + challenge.rightDiff * (rightSuccess - rightFailure)
        )
    )

    # this is for ongoing passive bonuses to other challenge difficulties
    bonusAmount = 0
    bonusIcons = []

    if challenge.effect == "spooky or magic challenges -1 difficulty":
        bonusAmount = -1
        bonusIcons = ["spooky", "magic"]
    if challenge.effect == "monster or trap challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["monster", "trap"]
    if challenge.effect == "spooky or magic challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["spooky", "magic"]
    if challenge.effect == "spooky challenges -1 difficulty":
        bonusAmount = -1
        bonusIcons = ["spooky"]
    if challenge.effect == "spooky challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["spooky"]
    if challenge.effect == "trap challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["trap"]
    if challenge.effect == "monster challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["monster"]
    if challenge.effect == "magic challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["magic"]
    if challenge.effect == "all challenges +1 difficulty":
        bonusAmount = 1
        bonusIcons = ["all"]
    if challenge.effect == "monster challenges -2 difficulty":
        bonusAmount = -2
        bonusIcons = ["monster"]

    if bonusAmount != 0:
        for outcome in allOutcomes:
            if outcome["card"] != challenge and (
                "all" in bonusIcons
                or any(icon in outcome["card"].icons for icon in bonusIcons)
            ):
                diffFactor += (
                    state.priorities["next turn relevance factor"]
                    * 0.15
                    * bonusAmount
                    * (outcome["success"] - outcome["failure"])
                )
    if challenge.effect == "flip at end of turn":
        # no need to disincentivize clearing this card since it will clear
        # at the end of the turn anyway.
        diffFactor = 0

    success += diffFactor
    if challenge.failEffect == "discard after damage":
        failure += diffFactor

    # need to put this here since calculateOutcomes doesn't know helpers
    if challenge.failEffect == "all players discard action tokens":
        for player in localState.players:
            if player.hasToken and player not in pcsSpendingTokens:
                failure -= player.getHoldTokenPriority(localState)

    locationCard = localState.locationDeck[0]
    if locationCard.failAnyEffect == "discard self":
        # if the location deck is train or race
        relicSuccess, relicFailure = getOutcomes(localState.relicDeck[0], allOutcomes)
        trainRaceDiffFactor = (
            state.priorities["next turn relevance factor"]
            * 0.15
            * (locationCard.leftDiff * (relicSuccess - relicFailure))
        )

        # this is for ongoing passive bonuses to other challenge difficulties
        bonusAmount = 0
        bonusIcons = []

        if locationCard.effect == "spooky or magic challenges -1 difficulty":
            bonusAmount = -1
            bonusIcons = ["spooky", "magic"]
        if locationCard.effect == "monster or trap challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["monster", "trap"]
        if locationCard.effect == "spooky or magic challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["spooky", "magic"]
        if locationCard.effect == "spooky challenges -1 difficulty":
            bonusAmount = -1
            bonusIcons = ["spooky"]
        if locationCard.effect == "spooky challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["spooky"]
        if locationCard.effect == "trap challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["trap"]
        if locationCard.effect == "monster challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["monster"]
        if locationCard.effect == "magic challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["magic"]
        if locationCard.effect == "all challenges +1 difficulty":
            bonusAmount = 1
            bonusIcons = ["all"]
        if locationCard.effect == "monster challenges -2 difficulty":
            bonusAmount = -2
            bonusIcons = ["monster"]

        if bonusAmount != 0:
            for outcome in allOutcomes:
                if outcome["card"] != locationCard and (
                    "all" in bonusIcons
                    or any(icon in outcome["card"].icons for icon in bonusIcons)
                ):
                    trainRaceDiffFactor += (
                        state.priorities["next turn relevance factor"]
                        * 0.15
                        * bonusAmount
                        * (outcome["success"] - outcome["failure"])
                    )

        failure += trainRaceDiffFactor
    if "win monster challenge" in [
        helper.discardEffect for helper in helpers if isinstance(helper, FKCCard)
    ]:
        return success - holdPriorityHelpers, success, failure
    if "any challenge 50%" in [
        helper.discardEffect for helper in helpers if isinstance(helper, FKCCard)
    ]:
        return (
            0.5 * success + 0.5 * failure - holdPriorityHelpers,
            success,
            failure,
        )
    if "no dice" in challenge.icons:
        if delta < 1:
            return (
                success - holdPriorityHelpers,
                success,
                failure,
            )
        else:
            return (
                failure - holdPriorityHelpers,
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
        prob * success
        + (1 - prob) * failure
        - holdPriorityHelpers
        + mightAsWellTryFactor,
        success,
        failure,
    )


def nextPlayer(localState=state):
    localState.currentPlayer += 1
    if localState.currentPlayer >= len(localState.players):
        localState.currentPlayer = 0
        for player in localState.players:
            player.hasToken = True  # bard tokens are handled elsewhere


def getActiveCards(localState=state):
    return [
        localState.villainDeck[0],
        localState.relicDeck[0],
        localState.locationDeck[0],
    ]


def getNumberOfAssistOpportunities(turnsRemaining=3, localState=state):
    if turnsRemaining > 3:
        turnsRemaining = 3
    activeCards = getActiveCards(localState)
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


def assembleOptions(localState=state, currentDeckType=""):
    options = []
    activeCards = getActiveCards(localState)
    lookAhead = localState == state

    def commonOptions(options, specialHelper):
        options.append(
            Option(
                card,
                pc,
                allOutcomes,
                helpers=[specialHelper],
                lookAhead=lookAhead,
            )
        )
        if "no assist" not in card.icons:
            for helper in beforeHelpers:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[specialHelper, helper],
                        lookAhead=lookAhead,
                    )
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
                    allOutcomes,
                    helpers=[
                        specialHelper,
                        Ability("wizard ability", pc),
                    ],
                    lookAhead=lookAhead,
                )
            )
            if "no assist" not in card.icons:
                for helper in beforeHelpers:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[
                                specialHelper,
                                Ability("wizard ability", pc),
                                helper,
                            ],
                            lookAhead=lookAhead,
                        )
                    )
            if strengthPotion is not None:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[
                            specialHelper,
                            Ability("wizard ability", pc),
                            strengthPotion,
                        ],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[
                                    specialHelper,
                                    Ability("wizard ability", pc),
                                    strengthPotion,
                                    helper,
                                ],
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
                    allOutcomes,
                    helpers=[
                        specialHelper,
                        Ability("warrior ability", pc),
                    ],
                    lookAhead=lookAhead,
                )
            )
            if "no assist" not in card.icons:
                for helper in beforeHelpers:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[
                                specialHelper,
                                Ability("warrior ability", pc),
                                helper,
                            ],
                            lookAhead=lookAhead,
                        )
                    )
            if strengthPotion is not None:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[
                            specialHelper,
                            Ability("warrior ability", pc),
                            strengthPotion,
                        ],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[
                                    specialHelper,
                                    Ability("warrior ability", pc),
                                    strengthPotion,
                                    helper,
                                ],
                                lookAhead=lookAhead,
                            )
                        )

        if strengthPotion is not None:
            options.append(
                Option(
                    card,
                    pc,
                    allOutcomes,
                    helpers=[specialHelper, strengthPotion],
                    lookAhead=lookAhead,
                )
            )
            if "no assist" not in card.icons:
                for helper in beforeHelpers:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[
                                specialHelper,
                                strengthPotion,
                                helper,
                            ],
                            lookAhead=lookAhead,
                        )
                    )

    # if looking ahead, skip the deck the current player is considering.
    # unless this player is bard and 'currentDeckType' is 'relic',
    # because that will likely be the bard's best option.
    for card in activeCards:
        if card.currentDeck == currentDeckType:
            activeCards.remove(card)
            break

    pc = localState.players[localState.currentPlayer]
    if (
        currentDeckType == "villain"
        and not deckDefeated("villain")
        and (oneDeckClear(localState) or state.location in ["train", "race"])
    ):
        activeCards.append(
            ChallengeCard(
                deck=state.villain,
                decktype="villain",
                name="[Generic Villain Card]",
                difficulty=8,
                loot=2,
                damage=2,
            )
        )
    if (
        currentDeckType == "relic"
        and not deckDefeated("relic")
        and (
            pc.name == "bard"
            or oneDeckClear(localState)
            or state.location in ["train", "race"]
        )
    ):
        activeCards.append(
            ChallengeCard(
                deck=state.relic,
                decktype="relic",
                name="[Generic Relic Card]",
                difficulty=8,
                loot=2,
                damage=2,
            )
        )

    if (
        currentDeckType == "location"
        and oneDeckClear(localState)
        and not deckDefeated("location")
        and state.location not in ["train", "race"]
    ):
        activeCards.append(
            ChallengeCard(
                deck=state.location,
                decktype="location",
                name="[Generic Location Card]",
                difficulty=8,
                loot=2,
                damage=2,
            )
        )

    allOutcomes = getAllOutcomes(activeCards, lookAhead)

    beforeHelpers = [
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
    beforeHelpersAll = [
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
        options.append(
            Option(localState.surprise, pc, allOutcomes, lookAhead=lookAhead)
        )
    for fkcCard in pc.fkcCards:
        if fkcCard.ongoingEffect == "recover 1 skip challenge":
            options.append(Option(fkcCard, pc, allOutcomes, lookAhead=lookAhead))
    for card in activeCards:
        if card.effect == "can discard fkc card to succeed" and pc.fkcCards:
            for fkcCard in pc.fkcCards:
                options.append(
                    Option(
                        fkcCard, pc, allOutcomes, helpers=[card], lookAhead=lookAhead
                    )
                )
        if (
            not (card.effect == "spend action token to engage" and not pc.hasToken)
            and not (card.finale and card.difficulty == 0)
            and not "no dice" in card.icons
        ):
            # consider the option of getting tokens back from Binicorn or Ring of Recall
            options.append(Option(card, pc, allOutcomes, lookAhead=lookAhead))
            if "no assist" not in card.icons:
                for helper in beforeHelpers:
                    options.append(
                        Option(
                            card, pc, allOutcomes, helpers=[helper], lookAhead=lookAhead
                        )
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
                        allOutcomes,
                        helpers=[Ability("wizard ability", pc)],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[Ability("wizard ability", pc), helper],
                                lookAhead=lookAhead,
                            )
                        )
                if strengthPotion is not None:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[Ability("wizard ability", pc), strengthPotion],
                            lookAhead=lookAhead,
                        )
                    )
                    if "no assist" not in card.icons:
                        for helper in beforeHelpers:
                            options.append(
                                Option(
                                    card,
                                    pc,
                                    allOutcomes,
                                    helpers=[
                                        Ability("wizard ability", pc),
                                        strengthPotion,
                                        helper,
                                    ],
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
                        allOutcomes,
                        helpers=[Ability("warrior ability", pc)],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[Ability("warrior ability", pc), helper],
                                lookAhead=lookAhead,
                            )
                        )
                if strengthPotion is not None:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[Ability("warrior ability", pc), strengthPotion],
                            lookAhead=lookAhead,
                        )
                    )
                    if "no assist" not in card.icons:
                        for helper in beforeHelpers:
                            options.append(
                                Option(
                                    card,
                                    pc,
                                    allOutcomes,
                                    helpers=[
                                        Ability("warrior ability", pc),
                                        strengthPotion,
                                        helper,
                                    ],
                                    lookAhead=lookAhead,
                                )
                            )

            if strengthPotion is not None:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[strengthPotion],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[strengthPotion, helper],
                                lookAhead=lookAhead,
                            )
                        )
            if card.effect == "can sac. up to 6 health for +1 before roll":
                for sacrifice in range(1, 7):
                    sacrificeHelper = SpecialHelper("sacrifice health", sacrifice)
                    commonOptions(options, sacrificeHelper)

            if coin is not None:
                options.append(
                    Option(card, pc, allOutcomes, helpers=[coin], lookAhead=lookAhead)
                )

            if swordOfDoom is not None and "monster" in card.icons:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[swordOfDoom],
                        lookAhead=lookAhead,
                    )
                )
            if ringOfRecall is not None and "no assist" not in card.icons:
                for helper in beforeHelpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[ringOfRecall, helper],
                            lookAhead=lookAhead,
                        )
                    )
            if (
                localState.surprise is not None
                and localState.surprise.discardEffect == "regain action tokens"
                and "no assist" not in card.icons
            ):

                for helper in beforeHelpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[localState.surprise, helper],
                            lookAhead=lookAhead,
                        )
                    )
        if (
            (card.effect == "spend action token to engage" and not pc.hasToken)
            and not (card.finale and card.difficulty == 0)
            and not "no dice" in card.icons
        ):
            if (
                localState.surprise is not None
                and localState.surprise.discardEffect == "regain action tokens"
            ):
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[localState.surprise],
                        lookAhead=lookAhead,
                    )
                )
                for helper in beforeHelpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[localState.surprise, helper],
                            lookAhead=lookAhead,
                        )
                    )
            if strengthPotion is not None:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[strengthPotion],
                        lookAhead=lookAhead,
                    )
                )
                if "no assist" not in card.icons:
                    for helper in beforeHelpers:
                        options.append(
                            Option(
                                card,
                                pc,
                                allOutcomes,
                                helpers=[strengthPotion, helper],
                                lookAhead=lookAhead,
                            )
                        )
            if coin is not None:
                options.append(
                    Option(card, pc, allOutcomes, helpers=[coin], lookAhead=lookAhead)
                )

            if swordOfDoom is not None and "monster" in card.icons:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[swordOfDoom],
                        lookAhead=lookAhead,
                    )
                )
            if ringOfRecall is not None:
                options.append(
                    Option(
                        card,
                        pc,
                        allOutcomes,
                        helpers=[ringOfRecall],
                        lookAhead=lookAhead,
                    )
                )
                for helper in beforeHelpersAll:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=[ringOfRecall, helper],
                            lookAhead=lookAhead,
                        )
                    )
        if "no dice" in card.icons and not (card.finale and card.difficulty == 0):
            minimumNeeded = getDelta(card, pc)
            if minimumNeeded <= 0:
                options.append(Option(card, pc, allOutcomes, lookAhead=lookAhead))
            else:
                currentDeck = getDeckFromType(card.currentDeck)
                maxAssists = 1
                if "double assist" in card.icons:
                    maxAssists = 2
                if "no assist" in card.icons:
                    maxAssists = 0
                assists = 0
                potentialHelpers = []
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
                    potentialHelpers.append(Ability("wizard ability", pc))
                if (
                    pc.name == "warrior"
                    or (
                        "can use other players abilities"
                        in [fkcCard.ongoingEffect for fkcCard in pc.fkcCards]
                        and "warrior" in [pc.name for pc in localState.players]
                    )
                ) and pc.hasToken:
                    potentialHelpers.append(Ability("warrior ability", pc))
                if localState.surprise is not None and (
                    "any die roll" in localState.surprise.discardEffect
                    or (
                        "trap die roll" in localState.surprise.discardEffect
                        and "trap" in card.icons
                    )
                    or (
                        "monster die roll" in localState.surprise.discardEffect
                        and "monster" in card.icons
                    )
                    or (
                        "spooky die roll" in localState.surprise.discardEffect
                        and "spooky" in card.icons
                    )
                    or (
                        "magic die roll" in localState.surprise.discardEffect
                        and "magic" in card.icons
                    )
                ):
                    potentialHelpers.append(localState.surprise)
                for fkcCard in pc.fkcCards:
                    if "any die roll before" in fkcCard.discardEffect:
                        potentialHelpers.append(fkcCard)
                for player in localState.players:
                    if (
                        player.hasToken
                        and (
                            "no assist"
                            not in [
                                fkcCard.ongoingEffect for fkcCard in player.fkcCards
                            ]
                        )
                        and (
                            player != pc
                            or "assist self"
                            in [fkcCard.ongoingEffect for fkcCard in player.fkcCards]
                        )
                        and maxAssists > 0
                    ):
                        potentialHelpers.append(player)
                    for fkcCard in player.fkcCards:
                        if (
                            "any die roll any player" in fkcCard.discardEffect
                            or (
                                "trap die roll any player" in fkcCard.discardEffect
                                and "trap" in card.icons
                            )
                            or (
                                "monster die roll any player" in fkcCard.discardEffect
                                and "monster" in card.icons
                            )
                            or (
                                "spooky die roll any player" in fkcCard.discardEffect
                                and "spooky" in card.icons
                            )
                            or (
                                "magic die roll any player" in fkcCard.discardEffect
                                and "magic" in card.icons
                            )
                        ):
                            potentialHelpers.append(fkcCard)

                def makeSetsOfUsefulHelpers(
                    setsOfUsefulHelpers, potentialHelpers, newSet
                ):
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
                            <= maxAssists
                        ):
                            helpSum = 0
                            for helper in newSet:
                                helpSum += helper.getAssistBefore(card.icons)
                                if isinstance(helper, FKCCard) or isinstance(
                                    helper, SurpriseCard
                                ):
                                    helpSum += helper.getAssistAfter(card.icons)
                            if helpSum >= minimumNeeded:
                                setsOfUsefulHelpers.append(newSet.copy())
                            else:
                                makeSetsOfUsefulHelpers(
                                    setsOfUsefulHelpers,
                                    potentialHelpers[index + 1 :],
                                    newSet,
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

                if setsOfUsefulHelpers:
                    options.append(
                        Option(
                            card,
                            pc,
                            allOutcomes,
                            helpers=setsOfUsefulHelpers[0],
                            lookAhead=lookAhead,
                        )
                    )

    options = sorted(options, reverse=True)
    if not options:
        if state.display:
            print("No options possible! Skipping turn.")
        options.append(Option(None, pc))
    return options


def getCardDeckChangePriority(decktype, changeAmt, localState=state):
    # priority of adding (positive changeAmt) or removing (negative)
    # challenge cards on a deck

    c1a = state.priorities["clear 1 card a"]
    c1b = state.priorities["clear 1 card b"]

    # villain deck length, relic deck length, location deck length
    vdl = len(localState.villainDeck)
    if vdl > 7 and isinstance(localState.villainDeck[-7], SurpriseCard):
        vdl -= 1
    rdl = len(localState.relicDeck)
    if rdl > 7 and isinstance(localState.relicDeck[-7], SurpriseCard):
        rdl -= 1
    ldl = len(localState.locationDeck)
    if ldl > 7 and isinstance(localState.locationDeck[-7], SurpriseCard):
        ldl -= 1

    if state.location not in ["train", "race"]:

        def inverseWithC1B(vdl, rdl, ldl):
            return 1 / (rdl + min(vdl, ldl) + c1b)

        startingValue = inverseWithC1B(vdl, rdl, ldl)

        if decktype == "villain":
            return c1a * (inverseWithC1B(vdl + changeAmt, rdl, ldl) - startingValue)
        if decktype == "relic":
            return c1a * (inverseWithC1B(vdl, rdl + changeAmt, ldl) - startingValue)
        if decktype == "location":
            return c1a * (inverseWithC1B(vdl, rdl, ldl + changeAmt) - startingValue)
        return None
    else:

        def inverseWithC1BAlt(vdl, rdl):
            return 1 / (rdl + vdl + c1b)

        startingValue = inverseWithC1BAlt(vdl, rdl)

        if decktype == "villain":
            return c1a * (inverseWithC1BAlt(vdl + changeAmt, rdl) - startingValue)
        if decktype == "relic":
            return c1a * (inverseWithC1BAlt(vdl, rdl + changeAmt) - startingValue)
        if decktype == "location":
            return getHealthChangePriority(ldl - 1, ldl + changeAmt - 1)
        return None


def getCardClearPriority(decktype, localState=state):
    # priority to remove one card from a challege deck
    return getCardDeckChangePriority(decktype, -1, localState)


def getCardAddPriority(decktype, localState=state):
    # priority to add a card back to a challenge deck
    return getCardDeckChangePriority(decktype, -1, localState)


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
    futureState.relicCounters = state.relicCounters
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
