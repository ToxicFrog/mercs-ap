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

def suit_to_chapter(suit):
  return {'clubs': 1, 'diamonds': 2, 'hearts': 3, 'spades': 4}[suit]


class GenericIntelItem(NamedTuple):
  id: int
  suit: str = None

  def name(self):
    if self.suit:
      return f'{self.suit.capitalize()} Intel'
    else:
      return 'Progressive Intel'

  def count(self, options):
    return 0

  def intel_amount(self):
    return 1

  def classification(self):
    return ItemClassification.progression

  def groups(self):
    return {'intel', 'progression'}


class CardIntelItem(NamedTuple):
  id: int
  rank: int
  suit: str
  rank_names = [None, None, 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

  def name(self):
    if self.suit:
      return f'{self.suit.capitalize()} Intel [{self.rank_names[self.rank]}]'
    elif rank > 10:
      return f'Progressive Intel [Face]'
    else:
      return f'Progressive Intel [{self.rank_names[self.rank]}]'

  def count(self, options):
    if not self.suit:
      return 0
    if suit_to_chapter(self.suit) <= options.goal:
      return 1
    return 0

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


class MoneyItem(NamedTuple):
  id: int
  amount: int

  def name(self):
    return f'${self.amount:,d}'

  def count(self, options):
    return 0

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'money', 'filler'}


CARD_INTEL = set()
GENERIC_INTEL = set()
MONEY = {MoneyItem(next_id(), amount) for amount in [50_000, 100_000, 250_000, 500_000]}
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
  return chain(CARD_INTEL, GENERIC_INTEL, MONEY)

def all_progression_items():
  return all_items()

def item_by_name(name):
  return ITEMS_BY_NAME[name]

for suit in ['clubs', 'diamonds', 'hearts', 'spades', None]:
  GENERIC_INTEL.add(GenericIntelItem(next_id(), suit))
  for rank in range(2,14):
    CARD_INTEL.add(CardIntelItem(next_id(), rank, suit))

ITEMS_BY_NAME = {
  item.name(): item
  for item in all_items()
}
