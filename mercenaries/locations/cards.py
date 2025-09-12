"""
Logic for cards.

With the exception of the 2 of Clubs (available only during the tutorial, and
coterminous with A1 'Ante Up'), number cards are available only in their chapter.

Face cards become available in their chapter and remain so until the end of the
game, but are each linked to a specific mission.

Ace cards are available only in their chapter and are linked to a specific mission.
"""

from itertools import chain
from typing import NamedTuple

from BaseClasses import LocationProgressType

from ..id import next_id
from .missions import MISSIONS

CARDS = {}

class CardLocation(NamedTuple):
  id: int
  rank: int
  suit: str
  min_chapter: int
  max_chapter: int
  hint_mission: str # What mission gives you a hint for this card when completing it?
  mission: str = None
  rank_names = [None, 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

  def short_name(self):
    return f'{self.rank:d}{self.suit.capitalize()[0]}'

  def name(self):
    return f'Verify the {self.rank_names[self.rank]} of {self.suit.capitalize()}'

  def should_include(self, options):
    return self.min_chapter <= options.goal

  def progress_type(self, options):
    return LocationProgressType.DEFAULT

  def chapter(self, options):
    return self.min_chapter

  def groups(self):
    if self.rank == 1:
      return {'cards', 'ace_cards'}
    elif self.rank > 10:
      return {'cards', 'face_cards'}
    elif self.missable():
      return {'cards', 'number_cards', 'missable'}
    else:
      return {'cards', 'number_cards'}

  def missable(self):
    return self.max_chapter < 4

  def missed(self, world, state):
    return (
      not state.has(self.name(), world.player)
      and world.current_chapter(state) > self.max_chapter
    )

  def is_checked(self, game):
    return game.is_card_verified(self.suit, self.rank)

  def is_hintable(self, found):
    if not self.hint_mission:
      return False
    return MISSIONS[self.hint_mission].short_name() in found

  def access_rule(self, world):
    # If this card is located inside a mission, the card is accessible iff the
    # mission is.
    if self.mission:
      return MISSIONS[self.mission].access_rule(world)

    # Otherwise it's accessible if we've reached the card's chapter.
    # Chapters are handled by region membership, so we don't need to do anything
    # here.
    return lambda _: True

def mkcard(*args):
  return CardLocation(next_id(), *args)

# Fields are: id, min chapter, max chapter, rank, suit, associated mission if any
CARDS = {
  card.short_name(): card
  for card in [
    # Chapter 1: Clubs
    # Missions without hints: M3 K3 A3
    mkcard( 2, 'clubs', 0, 1, None, 'A1'),
    mkcard( 3, 'clubs', 1, 1, 'C1'),
    mkcard( 4, 'clubs', 1, 1, 'M1'),
    mkcard( 5, 'clubs', 1, 1, 'K1'),
    mkcard( 6, 'clubs', 1, 1, 'K2'),
    mkcard( 7, 'clubs', 1, 1, 'M2'),
    mkcard( 8, 'clubs', 1, 1, 'C2'),
    mkcard( 9, 'clubs', 1, 1, 'C3'),
    mkcard(10, 'clubs', 1, 1, 'A2'),
    mkcard(11, 'clubs', 1, 1, None, 'M3'),
    mkcard(12, 'clubs', 1, 1, None, 'C3'),
    mkcard(13, 'clubs', 1, 1, None, 'K3'),
    mkcard( 1, 'clubs', 1, 1, None, 'A3'),

    # Chapter 2: Diamonds
    # Missions without hints: C6 M6 A6
    mkcard( 2, 'diamonds', 2, 2, 'C4'),
    mkcard( 3, 'diamonds', 2, 2, 'M4'),
    mkcard( 4, 'diamonds', 2, 2, 'K4'),
    mkcard( 5, 'diamonds', 2, 2, 'K5'),
    mkcard( 6, 'diamonds', 2, 2, 'M5'),
    mkcard( 7, 'diamonds', 2, 2, 'C5'),
    mkcard( 8, 'diamonds', 2, 2, 'A4'),
    mkcard( 9, 'diamonds', 2, 2, 'A5'),
    mkcard(10, 'diamonds', 2, 2, 'K6'),
    mkcard(11, 'diamonds', 2, 2, None, 'K6'),
    mkcard(12, 'diamonds', 2, 2, None, 'M6'),
    mkcard(13, 'diamonds', 2, 2, None, 'C6'),
    mkcard( 1, 'diamonds', 2, 2, None, 'A6'),

    # Chapter 3: Hearts
    # Missions without hints: M9 K9 A9
    mkcard( 2, 'hearts', 3, 3, 'M7'),
    mkcard( 3, 'hearts', 3, 3, 'K7'),
    mkcard( 4, 'hearts', 3, 3, 'C7'),
    mkcard( 5, 'hearts', 3, 3, 'C8'),
    mkcard( 6, 'hearts', 3, 3, 'K8'),
    mkcard( 7, 'hearts', 3, 3, 'M8'),
    mkcard( 8, 'hearts', 3, 3, 'A7'),
    mkcard( 9, 'hearts', 3, 3, 'C9'),
    mkcard(10, 'hearts', 3, 3, 'A8'),
    mkcard(11, 'hearts', 3, 3, None, 'C9'),
    mkcard(12, 'hearts', 3, 3, None, 'K9'),
    mkcard(13, 'hearts', 3, 3, None, 'M9'),
    mkcard( 1, 'hearts', 3, 3, None, 'A9'),

    # Chapter 4: Spades
    # Missions without hints: M12 A11
    mkcard( 2, 'spades', 4, 4, 'K10'),
    mkcard( 3, 'spades', 4, 4, 'C10'),
    mkcard( 4, 'spades', 4, 4, 'M10'),
    mkcard( 5, 'spades', 4, 4, 'M11'),
    mkcard( 6, 'spades', 4, 4, 'C11'),
    mkcard( 7, 'spades', 4, 4, 'K11'),
    mkcard( 8, 'spades', 4, 4, 'A10'),
    mkcard( 9, 'spades', 4, 4, 'C12'),
    mkcard(10, 'spades', 4, 4, 'K12'),
    mkcard(11, 'spades', 4, 4, None, 'M12'),
    mkcard(12, 'spades', 4, 4, None, 'C12'),
    mkcard(13, 'spades', 4, 4, None, 'K12'),
    mkcard( 1, 'spades', 4, 4, None, 'A11'),
  ]
}
