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

Progression items are Ace intel -- which can be configured to be suited or
progressive, and to use the vanilla intel amounts or a fixed number of 'intel
tokens' per Ace -- and Merchant of Menace unlocks. Duplicate shop unlocks act as
a stacking discount for the item in question.

Filler items are cash bonuses (ranging from $50k to $500k), permanent faction
reputation increases (with diminishing returns), and shop discounts (10% to 30%,
automatically applied to your most expensive item).

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
  - Shop coupons
  - Character skins
  - Health/ammo/grenade refills
- Improved logic:
  - Better mission logic, e.g. missions that want anti-air depending on having
    an AA vehicle, supply drop, or airstrike unlocked
