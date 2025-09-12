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


FILLER = {
  # Weights are based on how many of these are in the vanilla reward pool
  # x2 so money is a bit more common than reputation bonuses, about 6:1
  MoneyItem(next_id(), 2*1, 50_000),
  MoneyItem(next_id(), 2*4, 100_000),
  MoneyItem(next_id(), 2*6, 250_000),
  MoneyItem(next_id(), 2*2, 500_000),
  ReputationItem(next_id(), 1, 'Allies'),
  ReputationItem(next_id(), 1, 'Mafia'),
  ReputationItem(next_id(), 1, 'China'),
  ReputationItem(next_id(), 1, 'SK'),
}
