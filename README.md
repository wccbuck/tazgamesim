# tazgamesim
Simulation project for [the Adventure Zone board game](https://www.twogetherstudios.com/products/the-adventure-zone-bureau-of-balance-game-us-canada)

The goal of the Adventure Zone board game is to complete all ten challenges in the Relic challenge deck, as well as all ten challenges in either the Villain or the Location deck (with the exception of the Train and Race decks). Since the different decks present different levels of challenge, especially when played in certain combinations, the goal of this simulation project is to create a tool that can analytically assess their differences.

## How to use this tool

First, install pyyaml: `pip install pyyaml`. If you don't have pip, read how to get it [here](https://pip.pypa.io/en/stable/installation/).

Open `game_setup.yaml` and choose your villain, relic, and location. You have six options for each:

| Villain   | Relic | Location |
| --------- | ----- | -------- |
| lich      | staff | cave     |
| giant     | ring  | tomb     |
| crew      | sword | temple   |
| dark lord | sash  | carnival |
| dragon    | hoard | train    |
| cult      | idol  | race     |

Next, choose your players. Choose between three and five of the following options:

* bard, priest, rogue, warrior, wizard

Finally, choose whether you want to simulate one game at a time with a visual aid, or simulate many for statistical analysis. This is decided with the "display" option; `True` means you will see each step of the game in the terminal window, and `False` means you will only see indicators of games completed and cumulative win rates (once every ten games). Enter your desired number of games under "runs" (minimum 1). At the end of an "analytical mode" run (with display = False), you'll see a display of a variety of statistics, such as final win rate, average turn count, and more.

When display = True, you can also choose whether or not you want to "skipPauses". When set to True, the entire game will run to its conclusion at once; when set to False, the simulation will pause at certain points each turn and require the user to press "Enter" to continue.

Once you're all set up, just run `python3 run.py`. The simulator can complete one to two games per second on a fast computer.

## How Does This Work?

This simulation tool uses a priority-based logic to analyze options available to it each turn. When it is a certain player character (PC)'s turn, the tool will assess that PC's strength (and corresponding chance to succeed) versus each of the available challenge cards. It of course includes any passive bonuses from "Fantasy KostCo" cards, "Surprise" cards, and active challenge cards. The tool also assesses a variety of permutations of those options in which resources (action tokens, "Fantasy KostCo" cards, "Surprise" cards, etc) are expended to improve results, weighing the relative value of expending those resources against the anticipated change in outcome.

In addition, for each option, the tool glances ahead at the next player's turn, generates a brand-new set of options (though in a stripped-down way without any information that would ordinarily be hidden from actual human players in a normal game), assesses the best one, and returns it, adding it to the current player's option's priority score. In this way, the tool can make a pretty good guess of the best play for this turn that will also create the best situation for next turn.

I've spent some time and effort tweaking and improving the priority calculations, and while I think they certainly can be further improved, my goal for this project was never to "solve" the Adventure Zone game or to create the perfect bot, but rather to make a simulation tool that would make mostly-logical choices that reflect how humans might rationally play this game. And so, I've made a tool that can let me play hundreds of thousands (millions?) of games to analytically answer questions like "how many turns on average does a lich/idol/tomb game take to finish?", or "how much harder is a game with the hoard relic if the Nemesis doesn't show up early?"

## Assumptions

I had to make several assumptions in the creation of this tool. First and foremost: "Story +1" bonuses are always applied. I assume when you play this game at home that you are also always awarding story bonuses when someone puts in the effort. It is a collaborative storytelling game, after all.

### Using FKC card and Surprise discard abilities
Whenever a player character draws a third Fantasy KostCO (FKC) card, or whenever the players uncover a Surprise when one is already in play, the game says one of the excess needs to be discarded by the end of the turn. In my home game (and in this simulation), the discard ability of the card triggers on these end-of-turn discards.

### Max Health is Starting Health
The rulebook says this about health under Mission Setup: “Place a token on the team health track at the top of the game board. Starting Team Health depends on the number of players. For 2 players, start at 14 Health; for 3 players, start at 12 Health; for 4 or 5 players, start at 10 Health.”

It doesn’t explicitly say that playing with 4 or 5 players means that you can’t heal above 10. However, I assumed that to be the case; you can’t have 11 health with 5 players. It just doesn’t make sense to me for the reclaimers to land on site and the priest can immediately heal up on turn 1.

### Train/Race Decks
When playing with the Train or the Race as your location deck, one location card is discarded each time any player fails any challenge, and when you reach the finale, you lose the game. You must complete the Villain and Relic decks to win.

These decks are insanely difficult (like 33% win rate difficult). Essentially you can only fail 8 times total before you lose, in addition to having ⅓ fewer options for challenge decks and a diminished ability to accurately plan ahead turns. When I actually play these decks, I have a house rule where you can discard your action token in place of discarding the location challenge card on a failed attempt, which increases the win rate but not by a whole lot. You can enable this option in the simulation by setting "trainRaceTokenHouseRule" to "True" in game_setup.yaml.

### Dark Lord “Gerblin” Effects
Some cards in the Dark Lord deck can bring back a discarded challenge card with “Gerblin” in the title to this deck. I assumed these also work on the Cave deck’s “Gerblin Garrison” and the Carnival deck’s “Gerblin Pickpockets”. This is rules-as-written, and I saw no reason to make it restricted to Dark Lord cards. Because of these cases where a location card can be in a villain deck, I made a separate property of all challenge cards, “currentDeck”, completely distinct from “deck” and ”decktype”.

### Wandering Merchant (Hoard Card) and Fantasy Gachapon (Carnival Card)
It's not 100% clear how the dynamic works. “Effect: When you defeat this challenge, you (or for Fantasy Gachapon: each player) may discard a Fantasy KostCo card (if you have one) and draw a new one.”

So if I don’t have a FKC card, I can draw one anyway? Can I use the discard ability on the card I discard? If the answer to both of those questions is “no” (which I think it is, based on how it’s written), then this card’s effect isn't very strong and is unlikely to dramatically affect the outcome of a game. The relative value of losing a low-value card with an ongoing benefit for a new random card is difficult to calculate. My app ignores this effect entirely.

### Gift Shop (Hoard Card)
"Effect: While this card is in play, you can purchase a Fantasy KostCo card for 2 loot instead of the usual 3. If you do, flip this card and place a counter on the Hoard mission."

Ok… so the choice is, if I have 2 loot already, I can essentially gain 1 loot, in exchange for replacing the Gift Shop for a different relic card (Autograph Hounds) that grants 1 less loot than the Gift Shop (which grants 2 loot on defeat). So no real gain; I need to clear one of these to win the game, and each side gives 2 loot. Autograph Hounds isn’t easier to beat (in fact it can be harder if you’ve encountered the Nemesis). It adds 1 to the Villain difficulty until cleared. And flipping the Gift Shop also makes Nemesis more difficult.

Why on earth would I ever choose to flip Gift Shop? It might be worth considering if the FKC card cost reduced to 1. But as that’s not the case, my app entirely ignores this card’s effect.

### Nightmare Stalker (Cult Card)
The card reads “Effect: What nightmares must you battle?” That’s not an effect, so I assumed this was a typo and “Effect” should have read “Story +1”.
