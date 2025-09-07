from typing import Any, NamedTuple

from .pine import Pine
from .lopcode import LuaOpcode

class MemVar(NamedTuple):
  pine: Pine
  addr: int

class MemVarInt(MemVar):
  def __repr__(self):
    return f'MemVarInt(${self.addr:08X})'
  def __call__(self, val=None):
    if val is not None:
      self.pine.poke32(self.addr, val)
      return self()
    else:
      return self.pine.peek32(self.addr)

class MemVarInt16(MemVar):
  def __repr__(self):
    return f'MemVarInt16(${self.addr:08X})'
  def __call__(self, val=None):
    if val is not None:
      self.pine.poke16(self.addr, val)
      return self()
    else:
      return self.pine.peek16(self.addr)


class MemVarFloat(MemVar):
  def __repr__(self):
    return f'MemVarFloat(${self.addr:08X})'
  def __call__(self, val=None):
    if val is not None:
      self.pine.pokef32(self.addr, val)
      return self()
    else:
      return self.pine.peekf32(self.addr)

class MemVarOpcode(MemVar):
  def __repr__(self):
    return repr(self())
  def __call__(self, val=None):
    if val is not None:
      self.pine.poke32(self.addr, val.op)
      return self()
    else:
      return LuaOpcode(self.pine.peek32(self.addr))

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
