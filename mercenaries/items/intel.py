from typing import NamedTuple

from BaseClasses import ItemClassification

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
    elif self.rank > 10:
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

GENERIC_INTEL = {
  GenericIntelItem(next_id(), suit)
  for suit in ['clubs', 'diamonds', 'hearts', 'spades', None]
}

CARD_INTEL = {
  CardIntelItem(next_id(), rank, suit)
  for rank in range(2,14)
  for suit in ['clubs', 'diamonds', 'hearts', 'spades', None]
}
