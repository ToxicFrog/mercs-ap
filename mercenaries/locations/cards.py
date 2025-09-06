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

from ..id import next_id
from .missions import MISSIONS

CARDS = {}

class CardLocation(NamedTuple):
  id: int
  min_chapter: int
  max_chapter: int
  rank: int
  suit: str
  mission: str = None
  rank_names = [None, 'Ace', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Jack', 'Queen', 'King']

  def short_name(self):
    return f'{self.rank:d}{self.suit.capitalize()[0]}'

  def name(self):
    return f'Verify the {self.rank_names[self.rank]} of {self.suit.capitalize()}'

  def should_include(self, options):
    return self.min_chapter <= options.goal

  def chapter(self):
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

  def access_rule(self, world):
    # If this card is located inside a mission, the card is accessible iff the
    # mission is.
    if self.mission:
      return MISSIONS[self.mission].access_rule(world)

    # Otherwise it's accessible if we've reached the card's chapter.
    # Chapters are handled by region membership, so we don't need to do anything
    # here.
    return lambda _: True

# Fields are: id, min chapter, max chapter, rank, suit, associated mission if any
CARDS = {
  card.short_name(): card
  for card in chain(
    # Chapter 1: Clubs.
    # Two of Clubs is in the tutorial.
    [CardLocation(next_id(), 0, 4,    2, 'clubs', 'A1')],
    [CardLocation(next_id(), 1, 1, rank, 'clubs') for rank in range(3,11)],
    # Face cards are in Mafia, PRC, SK, and AN missions.
    [
      # TODO: face cards might become missable once we complete the ace, not just
      # number cards.
      CardLocation(next_id(), 1, 4, 11, 'clubs', 'M3'),
      CardLocation(next_id(), 1, 4, 12, 'clubs', 'C3'),
      CardLocation(next_id(), 1, 4, 13, 'clubs', 'K3'),
      CardLocation(next_id(), 1, 4,  1, 'clubs', 'A3'),
    ],
    # Chapter 2: Diamonds.
    [CardLocation(next_id(), 2, 2, rank, 'diamonds') for rank in range(2,11)],
    # Face cards are in SK, Mafia, PRC, and AN missions.
    [
      CardLocation(next_id(), 2, 4, 11, 'diamonds', 'K6'),
      CardLocation(next_id(), 2, 4, 12, 'diamonds', 'M6'),
      CardLocation(next_id(), 2, 4, 13, 'diamonds', 'C6'),
      CardLocation(next_id(), 2, 4,  1, 'diamonds', 'A6'),
    ],
    # Chapter 3: Hearts.
    # Face cards are in PRC, SK, Mafia, and AN missions.
    [CardLocation(next_id(), 3, 3, rank, 'hearts') for rank in range(2,11)],
    [
      CardLocation(next_id(), 3, 4, 11, 'hearts', 'C9'),
      CardLocation(next_id(), 3, 4, 12, 'hearts', 'K9'),
      CardLocation(next_id(), 3, 4, 13, 'hearts', 'M9'),
      CardLocation(next_id(), 3, 4,  1, 'hearts', 'A9'),
    ],
    # Chapter 4:
    [CardLocation(next_id(), 4, 4, rank, 'spades') for rank in range(2,11)],
    # Face cards are in Mafia, PRC, SK, and AN missions.
    [
      CardLocation(next_id(), 4, 4, 11, 'spades', 'M12'),
      CardLocation(next_id(), 4, 4, 12, 'spades', 'C12'),
      CardLocation(next_id(), 4, 4, 13, 'spades', 'K12'),
      CardLocation(next_id(), 4, 4,  1, 'spades', 'A11'),
    ],
  )
}
