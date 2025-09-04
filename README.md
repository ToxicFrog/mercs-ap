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

First of all, you'll need a US copy of "Mercenaries: Playground of Destruction",
serial number SLUS-20932. An unmodified disc image should have md5sum
`316ad24970b2f19558bc2bda7eb98d81`, but the randomizer is also compatible with
versions that have been patched to add subtitles, remove the splash screens, etc.




## Future Work

Some of these are speculative, and depend on reverse engineering I haven't done
yet to figure out if they're viable; this is a wishlist, not a roadmap.

- New checks:
  - Listening posts, national treasures, blueprints, and monuments
  - Mission bonus objectives
  - Challenges
- New items:
  - Shop discounts
  - Shop coupons
  - Reputation bonuses
  - Reputation floor increases
  - Character skins
  - Health/ammo/grenade refills
- Improved logic:
  - Better mission logic, e.g. missions that want anti-air depending on having
    an AA vehicle, supply drop, or airstrike unlocked
