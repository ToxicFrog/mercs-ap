from typing import Dict, List

from .pine import Pine
from .util import MemVarInt, MemVarArray

# Let's optimistically assume that these are in the right order and verify
# them when we play.
CLUBS_PTR    = 0x005240e4
DIAMONDS_PTR = 0x005242ec
HEARTS_PTR   = 0x005244f4
SPADES_PTR   = 0x005246fc

class DeckOf52:
  pine: Pine
  cards: Dict[str, List[MemVarInt]]

  def __init__(self, pine: Pine):
    self.pine = pine
    self.cards = {
      'clubs':    MemVarArray(pine, MemVarInt, CLUBS_PTR, 0x28, 13),
      'diamonds': MemVarArray(pine, MemVarInt, DIAMONDS_PTR, 0x28, 13),
      'hearts':   MemVarArray(pine, MemVarInt, HEARTS_PTR, 0x28, 13),
      'spades':   MemVarArray(pine, MemVarInt, SPADES_PTR, 0x28, 13),
    }

  def card_status(self, suit, rank):
    if rank == 1:
      # Aces are internally considered rank 14, above kings; rank 1 is empty
      rank = 14
    rank -= 2 # Arrays are zero-indexed and the 2 of X occupies index 0
    return self.cards[suit][rank]()

  def is_verified(self, suit, rank):
    return self.card_status(suit, rank) > 1

  def is_captured(self, suit, rank):
    return self.card_status(suit, rank) > 2

  def deck_status(self):
    return {
      suit: [self.card_status(suit, rank+1) for rank in range(13)]
      for suit in ['clubs', 'diamonds', 'hearts', 'spades']
    }
