from typing import Any

from .pine import Pine

class MemVarInt:
  pine: Pine
  addr: int
  def __init__(self, pine: Pine, addr: int):
    self.pine = pine
    self.addr = addr
  def __repr__(self):
    return f'MemVarInt(${self.addr:08X})'
  def __call__(self, val=None):
    if val is None:
      return self.pine.peek32(self.addr)
    else:
      return self.pine.poke32(self.addr, val)

def MemVarArray(pine: Pine, T: Any, base_ptr: int, size: int, count: int):
  return [
    T(pine, addr)
    for addr in [
      base_ptr + x*size for x in range(count)
    ]
  ]

def chapter_to_suit(chapter):
  # clubs are both 0 (tutorial) and 1
  return ['clubs', 'clubs', 'diamonds', 'hearts', 'spades'][chapter]
