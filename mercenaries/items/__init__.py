"""
Item catalogue for Mercenaries.

Currently, there are 99 checks (52 cards + 47 missions), some of them missable.

For items, we implement only the Merchant of Menace unlocks (63 items); we fill
the rest with cash bonuses drawn from a similar distribution to the threshold
bonuses:
  1×  $50,000
  2× $100,000
  2× $250,000
  1× $500,000

In the future, the goal is to also add:
  - 48 intel awards (or a smaller, configurable number that is hard required to unlock the ace)
  - 11 skins
  - airstrike freebies
  - shop discounts
  - reputation bonuses
"""

from itertools import chain
from typing import NamedTuple

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region, Tutorial, LocationProgressType

from ..id import next_id

class GenericIntelItem(NamedTuple):
  id: int
  count: int
  suit: str = None

  def name(self):
    if self.suit:
      return f'Intel on the Ace of {self.suit.capitalize()}'
    else:
      return 'Progressive Ace Intel'

  def intel_amount(self):
    return 1

  def classification(self):
    return ItemClassification.progression

  def groups(self):
    return {'intel', 'progression'}


class CardIntelItem(NamedTuple):
  id: int
  count: int
  rank: int
  suit: str
  rank_names = [None, None, 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

  def name(self):
    return f'Intel from the {self.rank_names[self.rank]} of {self.suit.capitalize()}'

  # TODO: double check if these are the same numbers for later chapters
  def intel_amount(self):
    if self.rank <= 10:
      return self.rank
    else:
      return 30

  def classification(self):
    return ItemClassification.progression

  def groups(self):
    return {'intel', 'progression'}


CARD_INTEL = set()
GENERIC_INTEL = set()
global ITEMS_BY_NAME

def name_to_id_map():
  return {
    item.name(): item.id for item in all_items()
  }

def group_to_names_map():
  groups = {}
  for item in all_items():
    for group in item.groups():
      groups.setdefault(group, set()).add(item.name())
  return groups

def all_items():
  return chain(CARD_INTEL, GENERIC_INTEL)

def all_progression_items():
  return all_items()

def all_filler_items():
  return set()

def item_by_name(name):
  return ITEMS_BY_NAME[name]

GENERIC_INTEL.add(GenericIntelItem(next_id(), 1, None))
for suit in ['clubs', 'diamonds', 'hearts', 'spades']:
  GENERIC_INTEL.add(GenericIntelItem(next_id(), 1, suit))
  for rank in [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
    CARD_INTEL.add(CardIntelItem(next_id(), 1, rank, suit))

ITEMS_BY_NAME = {
  item.name(): item
  for item in all_items()
}
