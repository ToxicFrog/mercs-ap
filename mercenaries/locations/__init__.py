"""
Location catalogue for Mercenaries.

At the moment, the only locations implemented are:
- 52 cards
  - 4 aces
  - 12 face cards
  - 10 unmissable numbers (the tutorial 2C and the entire suit of spades)
  - 26 missable numbers (clubs, diamonds, and hearts)
- 47 missions
  - 11 allies, including 1 tutorial and 4 ace missions
  - 12 each SK, mafia, and chinese

In the future the desire is to also add:
- 36 collectable thresholds
- 301 individual collectables
  - 25+31 listening posts
  - 10+11 monuments
  - 53+57 treasures
  - 59+51 blueprints
- 16+13 challenges
"""

from itertools import chain

from .cards import CARDS
from .missions import MissionLocation, MISSIONS

def all_locations():
  return chain(CARDS.values(), MISSIONS.values())

LOCATIONS_BY_ID = { location.id: location for location in all_locations() }

def location_by_id(id: int):
  return LOCATIONS_BY_ID[id]

def mission(code: str) -> MissionLocation:
  return MISSIONS[code]

def name_to_id_map():
  return {
    location.name(): location.id for location in all_locations()
  }

def group_to_names_map():
  groups = {}
  for location in all_locations():
    for group in location.groups():
      groups.setdefault(group, set()).add(location.name())
  return groups

