# Mercenaries Archipelago

This is an [Archipelago Multiworld Randomizer](https://archipelago.gg) for the
PS2 game *Mercenaries: Playground of Destruction*.

## Overview

Instead of getting intel from Deck of 52 verifications and shop unlocks from
mission objectives, both missions and verifications can randomly reward intel,
shop unlocks, or money.

Intel behaviour can be customized: you can use a fixed number of "intel tokens"
per Ace rather than the vanilla card-based intel, and/or use progressive intel
that is not tied to a specific suit.

Monetary rewards from objectives are not randomized; money added to the pool as
filler is in addition to the money you earn by playing normally.

## Setup

### Prerequisites

- [Archipelago](https://archipelago.gg)
- The [apworld](./release/mercenaries.apworld)
- A **US** copy of "Mercenaries: Playground of Destruction"
  - Game ID is SLUS-20932, with mdsum `316ad24970b2f19558bc2bda7eb98d81`
  - Subtitles patch is supported
  - Other regions/languages are not supported
- [PCSX2](https://pcsx2.net/) to play it with
  - Real hardware not supported, sorry

### First-time setup

Get PCSX2 installed and running and make sure you can actually play Mercenaries
in it. Once you have that, open up `System -> Settings -> Advanced`, scroll to
the bottom, and tick `PINE Settings -> Enable`. Leave the `Slot` at the default
of 28011.

If your computer is sufficiently powerful, you may also want to go to
`Settings -> Game Properties -> Emulation` and set the `EE Cycle Rate` to 180%
or 300%; at default speeds Mercenaries tends to drop from 30fps to 20fps in
busy scenes, but it tolerates high clock rates well and if your computer can
keep up this should get you a consistent 30fps.

### Per-game setup

Configuration and generation works basically the same as any other AP game; see
the generated YAML for options. To join, just click `Mercenaries Client` in the
AP launcher and it should automatically connect to PCSX2.

## Gameplay

The game plays out more or less as usual, except that the intel
you need to take on the Ace at the end of each chapter is in the random item
pool, and the amount needed may be non-vanilla.

Mission completions and card verifications will randomly award intel, shop
unlocks, or bonus money (in addition to their vanilla monetary rewards).

### Known Issues

Due to limitations in the AP<->Mercs connection, item and check delivery does
not always happen immediately. In particular, some checks are not delivered to
AP until the next time you open your PDA, and most items cannot be delivered
unless you are on foot (i.e. not in a cutscene or a vehicle).

Intel items, additionally, will not appear in-game until the next time the game
checks your intel catalogue. This tends to happen naturally, but if you're
having trouble, completing a challenge or saving and then reloading your game
will probably work.


## Future Work

Some of these are speculative, and depend on reverse engineering I haven't done
yet to figure out if they're viable; this is a wishlist, not a roadmap.

- New checks:
  - Bounties: Listening posts, national treasures, blueprints, and monuments
  - Mission bonus objectives
  - Challenges
  - Vehicles driven/destroyed catalogue entries
- New items:
  - Shop coupons
  - Reputation bonuses
  - Reputation floor increases
  - Character skins
  - Health/ammo/grenade refills
- Improved logic:
  - Better mission logic, e.g. missions that want anti-air depending on having
    an AA vehicle, supply drop, or airstrike unlocked
