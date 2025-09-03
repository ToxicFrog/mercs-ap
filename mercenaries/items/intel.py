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
    if options.vanilla_intel:
      # Vanilla intel behaviour enabled, we will populate the pool with
      # CardIntelItems instead.
      return 0

    if bool(self.suit) == bool(options.progressive_intel):
      # Suited intel is not included in progressive intel mode, and vice versa.
      return 0

    if options.progressive_intel:
      return options.intel_in_pool
    elif suit_to_chapter(self.suit) > options.goal:
      return 0
    else:
      return options.intel_in_pool//options.goal

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
    else:
      return f'Progressive Intel [{self.rank_names[self.rank]}]'

  def count(self, options):
    if not options.vanilla_intel:
      # Intel tokens rather than vanilla intel behaviour.
      return 0

    if bool(self.suit) == bool(options.progressive_intel):
      # Suited intel is not included in progressive intel mode, and vice versa.
      return 0

    if options.progressive_intel:
      return options.goal # One copy per chapter
    elif suit_to_chapter(self.suit) > options.goal:
      return 0
    else:
      return 1 # 1 copy of each × 1 suit per chapter

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
