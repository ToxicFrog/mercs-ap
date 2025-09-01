import sys
import time

from pine import Pine
from lua import GCObject

pcsx2: Pine = Pine(path = '/run/user/8509/pcsx2.sock')

print(pcsx2.game_info())

Lptr = pcsx2.peek32(0x0056CBD0)
L = GCObject(pcsx2, Lptr)

seen = L.initialSeen()
seen[L._G.val.addr] = True

L.getglobal('util_PrintDebugMsg').dump(seen)
L.getglobal('table_Debug').dump(seen)

util_PrintDebugMsg = L.getglobal('util_PrintDebugMsg')
util_PrintDebugMsg.klist[0].val.setData(b'sDebugBuffer')

sys.exit(0)


clubs = [
  0x005240e4, 0x0052410c, 0x00524134, 0x0052415c, 0x00524184,
  0x005241ac, 0x005241d4, 0x005241fc, 0x00524224, 0x0052424c,
  0x00524274, 0x00524274, 0x0052429c,
]

old = None
def diff(val):
  global old
  if val != old:
    print('+', val)
    old = val

while True:
  diff(pcsx2.readmem(0x005241ac - 0x28, 0x28*2))
  time.sleep(0.1)

while True:
  new = [pcsx2.peek32(addr) for addr in clubs]
  if new != status:
    print(new)
    status = new
  time.sleep(1)

buf = None
while True:
  newbuf = pcsx2.readmem(0x579960, 64)
  if newbuf != buf:
    print('+', newbuf.decode(errors = 'ignore'))
    buf = newbuf
  time.sleep(0.1)

print(pcsx2.peek32(0x579b59), pcsx2.peek32(0x579a59))
print(pcsx2.peek32(0x005240e4))
print(pcsx2.peek32(0x0052410c))
