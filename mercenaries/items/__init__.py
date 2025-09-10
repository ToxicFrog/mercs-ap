'''
Item catalogue for Mercenaries.

At present this means:
- intel (suited and progressive versions of vanilla and generic intel)
- money ($50k, $100k, $250k, and $500k, based on the bounty rewards)
- shop unlocks (can be duplicated, duplicates act as discounts)
'''

from itertools import chain
from typing import NamedTuple

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region, Tutorial, LocationProgressType

from ..id import next_id
from .intel import CARD_INTEL, GENERIC_INTEL
from .shop import SHOP_ITEMS

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


MONEY = {MoneyItem(next_id(), amount) for amount in [50_000, 100_000, 250_000, 500_000]}

def all_items():
  return chain(CARD_INTEL, GENERIC_INTEL, SHOP_ITEMS, MONEY)

def all_items_in_groups(groups):
  return (item for item in all_items() if item.groups() >= groups)

ITEMS_BY_NAME = { item.name(): item for item in all_items() }
ITEMS_BY_ID = { item.id: item for item in all_items() }

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

def all_progression_items():
  return all_items()

def item_by_name(name):
  return ITEMS_BY_NAME[name]

def item_by_id(id):
  return ITEMS_BY_ID[id]
