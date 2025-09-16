from typing import NamedTuple

from BaseClasses import ItemClassification

from ..id import next_id
from ..data import shopdata

class ShopItem(NamedTuple):
  id: int
  tag: int   # Internal tag used by the engine to represent this
  price: int # Base price before reputation modifiers
  template_groups: str
  template: str
  title: str  # User-facing name

  def name(self):
    return self.title

  def count(self, options):
    return int(options.shop_unlock_count)

  def groups(self):
    return {'progression', 'shop'} | self.template_groups

  def classification(self):
    return ItemClassification.progression


SHOP_ITEMS = [
  ShopItem(next_id(), u.tag, u.price, u.groups, u.template, u.name)
  for u in shopdata.UNLOCKS
]
