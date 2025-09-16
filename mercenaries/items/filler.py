from typing import NamedTuple

from BaseClasses import CollectionState, Item, ItemClassification, Location, MultiWorld, Region, Tutorial, LocationProgressType

from ..id import next_id


class MoneyItem(NamedTuple):
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
  id: int
  weight: int
  discount: int

  def name(self):
    return f'{self.discount}% Off'

  def count(self, options):
    return self.weight

  def classification(self):
    return ItemClassification.filler

  def groups(self):
    return {'shop', 'filler'}



FILLER = {
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
}

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