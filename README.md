# Mercenaries Archipelago

This is an [Archipelago Multiworld Randomizer](https://archipelago.gg) for the
PS2 game *Mercenaries: Playground of Destruction*.

## Features

### Checks

Completing missions and verifying members of the Deck of 52 will count as AP
checks. Collecting bounties will also produce checks, with the number of
bounties needed per check configurable in the yaml.

In all cases, the vanilla monetary and faction rewards are left intact; the AP
check replaces the shop unlock or Ace intel you would normally get.

Missable checks (most non-Ace cards and missions) will be auto-released at the
end of their corresponding chapter, so rushing for the Ace early once you have
enough intel and firepower is a viable strategy and will not lock you out of
chapter-specific checks.

### Items

#### Progression

**Ace intel.** This serves the same purpose as intel in the vanilla game.
Depending on your yaml settings, it can use the vanilla intel amounts or a fixed
number of "intel tokens" per ace, and it can be suited or progressive.

**Merchant of Menace unlocks.** These are the only way to unlock new things in the store. You can enable duplicates in the item pool, in which case picking up duplicate unlocks will give you a permanent discount on that item.

#### Filler

**Cash bonuses.** These range from $5k to $500k.

**Faction mood adjustments.** The more of these you have for a faction, the higher their minimum mood towards you is. There are diminishing returns as you collect more.

**Shop discounts.** These range from 10% to 30% off. They are permanent and are automatically applied to whatever your most expensive item is. As you get more expensive items the coupons will automatically be moved around.

**Free samples.** These apply to broad categories (e.g. "free airstrike") and will pick an appropriate random item from that category when issued to you. If you don't have at least three items in that category, they'll wait until you do. These samples are usually lost when you do anything involving a loading screen, so use it or lose it.

### Hints

Completing a mission that gives in-game hints about the location of a Number
will also give an AP hint for what item that Number is carrying.

Capturing a Card alive will give you a hint for a random progression item,
either someone else's in your world, or one of yours in someone else's world.


## Setup

### Prerequisites

- [Archipelago](https://archipelago.gg)
- The [apworld](./release/mercenaries.apworld)
- A **US** copy of "Mercenaries: Playground of Destruction", with game ID `SLUS-20932`
- [PCSX2](https://pcsx2.net/) to play it with
  - Real hardware not supported, sorry

### First-time setup

Get PCSX2 installed and running and make sure you can actually run Mercenaries
in it. Once you have that, change the following settings:
- `Tools -> Show Advanced Settings` **on**
- `System -> Settings -> Advanced -> PINE Settings -> Enable` **on**
- `System -> Settings -> Advanced -> PINE Settings -> Slot` **28011** (should be the default)

If your computer is sufficiently powerful, you may also want to open up
`Settings -> Game Properties -> Emulation` and set the `EE Cycle Rate` to 180%
or 300%; this will mess up the inter-chapter cutscenes, but allow the game to
maintain a steady 30fps during gameplay.

### Per-game setup

Configuration and generation works basically the same as any other AP game; see
the generated YAML for options. To join, just click `Mercenaries Client` in the
AP launcher and it should automatically connect to PCSX2.


## Known Issues and Limitations

Card verifications may not be registered by AP until the next time you open your
PDA in-game.

Messages and some items can only be delivered to Mercenaries at certain points
in execution, which means there may be a significant delay between getting
something in AP and it showing up in-game. This is particularly the case with
money, intel, and faction reputation adjustments. Wandering around the game and
doing things to force it to load/unload areas and NPCs tends to speed up this
process.

Combat logic only takes into account how many things you have unlocked, not what
things, e.g. it will not lock a mission where you fight helicopters behind
having access to anti-air support. Missions generally give you everything you
need on-site if you look around, so this is not a problem in practice.

Windows is not currently supported, and needs some changes to the emulator
connection code to function.

## Future Work

Some of these are speculative, and depend on reverse engineering I haven't done
yet to figure out if they're viable; this is a wishlist, not a roadmap.

- New checks:
  - Mission bonus objectives
  - Challenges
  - Vehicles driven/destroyed catalogue entries
- New items:
  - Character skins
  - Health/ammo/grenade refills
- Improved logic:
  - Better mission logic, e.g. missions that want anti-air depending on having
    an AA vehicle, supply drop, or airstrike unlocked
