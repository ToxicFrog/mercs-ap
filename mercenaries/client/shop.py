from math import floor
from typing import NamedTuple, List

from ..data.shopdata import *
from .pine import Pine
from .util import MemVarInt, MemVarArray

class ShopUnlock(NamedTuple):
  tag: MemVarInt
  price: MemVarInt
  new: MemVarInt

class MafiaShop:
  pine: Pine

  def __init__(self, pine: Pine):
    def mkUnlock(pine, addr):
      return ShopUnlock(
        MemVarInt(pine, addr),
        MemVarInt(pine, addr+4),
        MemVarInt(pine, addr+8))
    self.pine = pine
    self.unlock_count = MemVarInt(pine, METADATA_PTR)
    self.vehicle_count = MemVarInt(pine, METADATA_PTR+4)
    self.supplies_count = MemVarInt(pine, METADATA_PTR+8)
    self.airstrike_count = MemVarInt(pine, METADATA_PTR+12)
    self.unlocks = MemVarArray(pine, mkUnlock, UNLOCK_PTR, 12, NROF_UNLOCKS)

  def clear_unlocks(self):
    self.update_counts([])

  def update_counts(self, unlocks: List):
    self.vehicle_count(sum(1 for ul in unlocks if 'vehicle' in ul.groups()))
    self.supplies_count(sum(1 for ul in unlocks if 'supplies' in ul.groups()))
    self.airstrike_count(sum(1 for ul in unlocks if 'airstrike' in ul.groups()))
    self.unlock_count(len(unlocks))

  def set_unlocks(self, unlocks: List):
    # old_count = self.unlock_count()
    self.unlock_count(0)

    for idx,unlock in enumerate(unlocks):
      self.unlocks[idx].tag(unlock.tag)
      self.unlocks[idx].price(unlock.price)
      self.unlocks[idx].new(0) # TODO: maybe set this for new items (which aren't neccessarily at tail)

    self.update_counts(unlocks)
