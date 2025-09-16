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

  def apply_discount_coupons(self, contents, discounts):
    # Best discount at end so we can pop() it
    discounts = sorted(discounts, key=lambda x: x.discount)
    while len(discounts) > 0:
      # Repeatedly find the most expensive item in the shop, apply a discount
      # coupon to it, and discard the coupon.
      contents = sorted(contents, key=lambda x: x[1], reverse=True)
      discount = discounts.pop()
      contents[0][1] = floor(contents[0][1] * (discount.discount/100))

  def set_unlocks(self, unlocks: List[List[int]], discounts: List, discount_factor: float):
    old_count = self.unlock_count()
    self.unlock_count(0)

    shop_contents = []

    # Generate a list of shop entries in order of discovery, with discounts from
    # duplicate items factored in.
    for idx, (tag, count) in enumerate(unlocks):
      price = max(1, floor(UNLOCKS[tag].price * (discount_factor ** (count-1))))
      # Discounts don't apply to the Cheat Crate.
      if tag == 0x3D:
        continue
      elif idx >= old_count or self.unlocks[idx].tag() != tag:
        shop_contents.append([tag, price, True])
      else:
        shop_contents.append([tag, price, False])

    self.apply_discount_coupons(shop_contents, discounts)

    for idx,[tag, price, new] in enumerate(shop_contents):
      self.unlocks[idx].tag(tag)
      self.unlocks[idx].price(price)
      if new:
        print(f'+ {UNLOCKS[tag].name} ${UNLOCKS[tag].price:,d}')
        self.unlocks[idx].new(1)

    self.update_counts([unlock[0] for unlock in unlocks])
