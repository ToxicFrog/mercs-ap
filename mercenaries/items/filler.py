from typing import NamedTuple, Set

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region, Tutorial, LocationProgressType

from ..id import next_id


class MoneyItem(NamedTuple):
  '''
  A one-time cash bonus for the player.
  '''
  id: int
  weight: int
  amount: int

  def name(self):
    return f'${self.amount:,d}'

  def count(self, options):
    return self.weight

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'money', 'filler'}


class ReputationItem(NamedTuple):
  '''
  A reputation floor adjustment. The first two adjust the floor to -50 (faction
  will no longer withdraw missions or be shoot-on-sight to you) and then 0
  (faction will always be at least "neutral"). Subsequent adjusters give
  incremental bonuses to the floor, with diminishing returns.
  '''
  id: int
  weight: int
  faction_name: str

  def name(self):
    return f'{self.faction_name} reputation'

  def faction(self):
    return self.faction_name.lower()

  def count(self, options):
    return self.weight

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'reputation', 'filler'}


class DiscountItem(NamedTuple):
  '''
  A floating discount that applies to whatever the most expensive item in the
  shop is. Multiple discounts can stack but once enough have stacked that the
  item in question is no longer the most expensive, they'll start applying to
  something else.
  '''
  id: int
  weight: int
  discount: int

  def name(self):
    return f'{self.discount}% discount'

  def count(self, options):
    return self.weight

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'shop', 'filler'}


class CouponItem(NamedTuple):
  '''
  A coupon for a free Merchant of Menace delivery. Only applies to things you
  already have unlocked (due to technical difficulties). Come in generic "by
  item category" and "by faction" versions and give you a random thing from that
  faction/category.
  '''
  id: int
  weight: int
  title: str
  compatible: Set[str]

  def name(self):
    return f'Free {self.title}'

  def count(self, options):
    return self.weight

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'shop', 'filler'}

  def applies_to(self, shop_item):
    return shop_item.groups() & self.compatible


FILLER = [
  # Money bonuses, using the vanilla proportions for listening posts and monuments,
  # dropping the $3k bonuses for  BPs/treasures, and rearranging the bounty milestone
  # bonuses so the most valuable ones are also the rarest.
  # 90 in total.
  MoneyItem(next_id(), 56,  5_000),
  MoneyItem(next_id(), 21, 10_000),
  MoneyItem(next_id(),  6, 50_000),
  MoneyItem(next_id(),  4, 100_000),
  MoneyItem(next_id(),  2, 250_000),
  MoneyItem(next_id(),  1, 500_000),
  # Reputation floor items should be relatively rare.
  ReputationItem(next_id(), 2, 'Allies'),
  ReputationItem(next_id(), 2, 'Mafia'),
  ReputationItem(next_id(), 2, 'China'),
  ReputationItem(next_id(), 2, 'SK'),
  # Just kind of winging it with these tbh
  DiscountItem(next_id(), 16, 10), # Worth about 45k, in the endgame, with diminishing returns
  DiscountItem(next_id(), 8, 20), # 90k
  DiscountItem(next_id(), 4, 30), # 135k
  # And these
  CouponItem(next_id(), 8, 'airstrike', {'airstrike'}),
  CouponItem(next_id(), 8, 'supply drop', {'supplies'}),
  CouponItem(next_id(), 8, 'vehicle', {'vehicle'}),
  CouponItem(next_id(), 8, 'Allied item', {'allies'}),
  CouponItem(next_id(), 8, 'Chinese item', {'china'}),
  CouponItem(next_id(), 8, 'Mafia item', {'mafia'}),
  CouponItem(next_id(), 8, 'Korean item', {'sk', 'nk'}),
]

'''
Filler proportions in the main game

 56 x   $5,000  -- listening posts
110 x   $3,000  -- treasures
110 x   $3,000  -- blueprints
 21 x  $10,000  -- monuments
  1 x  $50,000  -- bounty milestone
  4 x $100,000  -- bounty milestone
  6 x $250,000  -- bounty milestone
  2 x $500,000  -- bounty milestone
 12 x unlock    -- bounty milestone
 10 x skins     -- bounty milestone
332 = total number of filler items

In a full game we have 396 locations. Using vanilla intel, we can break this
down thusly:

 48 deck intel
 63 shop unlocks
111 ==total progression items
285 ==filler slots left


'''