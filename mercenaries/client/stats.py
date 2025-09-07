from .pine import Pine
from .statsdata import *
from .util import MemVarFloat, MemVarArray, MemVarInt16

class PDAStats:
  def __init__(self, pine):
    self.pine = pine
    self.destruction = MemVarArray(pine, MemVarFloat, VEHICLES_DESTROYED_ADDR, 4, len(VEHICLE_NAMES))
    self.bounties = {
      name: MemVarInt16(pine, addr)
      for name,addr in BOUNTY_IDX_ADDRS.items()
    }

  def vehicles_destroyed(self):
    return {
      VEHICLE_NAMES[idx]
      for idx,count in enumerate(self.destruction)
      if count() > 0
    }

  def read_bounty_count(self, idx):
    if idx == 0:
      return 0
    buf = self.pine.readmem(BOUNTY_BUF_ADDR + idx, 8)
    buf = buf[:buf.find(0)]
    if len(buf) == 0:
      return 0
    return int(buf.decode())

  def bounties_found(self):
    return {
      name: self.read_bounty_count(idx())
      for name,idx in self.bounties.items()
    }
