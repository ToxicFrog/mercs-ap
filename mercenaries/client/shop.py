from math import floor
from typing import NamedTuple, List

from .pine import Pine
from .shopdata import *
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

  def update_counts(self, unlocks: List[int]):
    self.vehicle_count(sum(1 for id in unlocks if UNLOCKS[id].type == 'vehicle'))
    self.supplies_count(sum(1 for id in unlocks if UNLOCKS[id].type == 'supplies'))
    self.airstrike_count(sum(1 for id in unlocks if UNLOCKS[id].type == 'airstrike'))
    self.unlock_count(len(unlocks))

  def set_unlocks(self, unlocks: List[List[int]], discount_factor: float):
    old_count = self.unlock_count()
    self.unlock_count(0)

    for idx, (tag, count) in enumerate(unlocks):
      price = max(1, floor(UNLOCKS[tag].price * (discount_factor ** (count-1))))
      if idx >= old_count or self.unlocks[idx].tag() != tag:
        print(f'+ {UNLOCKS[tag].name} ${UNLOCKS[tag].price:,d}')
        self.unlocks[idx].new(1)
      self.unlocks[idx].tag(tag)
      self.unlocks[idx].price(price)
    self.update_counts([unlock[0] for unlock in unlocks])
