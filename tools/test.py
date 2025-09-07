import sys
import time

from .pine import Pine
from .lua import GCObject, TObject

pcsx2: Pine = Pine(path = '/run/user/8509/pcsx2.sock')

print(pcsx2.game_info())

# Lptr = pcsx2.peek32(0x0056CBD0)
# L = GCObject(pcsx2, Lptr)

# LPs: 50202a, 50202c
# BPs: 502be0, 502be2, 502be4
# PMs: 502202 ... 50220a?
# NTs: 502296..29e?

from .stats import PDAStats

stats = PDAStats(pcsx2)
print(stats.vehicles_destroyed())
print(stats.bounties_found())

def readCollectableCount(addr):
  idx = pcsx2.peek16(addr)
  if idx == 0:
    return ''
  ptr = 0xda38c0 + idx
  buf = pcsx2.readmem(ptr, 8)
  return buf[:buf.find(0)].decode()

for label,base in [
  ('LP', 0x50202a),
  ('BP', 0x502be0),
  ('PM', 0x502202),
  ('NT', 0x502294),
]:
  print(f'{label} ${base:08X} {[readCollectableCount(base+i*2) for i in range(8)]}')
  # print('indexes', [pcsx2.peek16(base+i*2) for i in range(8)])
  # print('pointers', ['%08X' % pcsx2.peek32(0xda38c0 + pcsx2.peek16(base+i*2)) for i in range(8)])

sys.exit(0)


base = 0x502020
for base in [0x50202a, 0x50202c, 0x502be0, 0x502be2, 0x502be4]:
  idx = pcsx2.peek16(base)
  ptr = 0xda38c0 + idx
  val = pcsx2.peek8(ptr)
  ptr2 = pcsx2.peek32(0xda38c0) + idx
  val2 = pcsx2.peek8(ptr2)
  print(f'{base:08X} {idx:5}')
  print(f'   ptr={ptr:08X} -> {[c for c in pcsx2.readmem(ptr-8, 8)]} {[c for c in pcsx2.readmem(ptr, 8)]} {pcsx2.readmem(ptr-8, 16)}')
  print(f'  ptr2={ptr2:08X} -> {[c for c in pcsx2.readmem(ptr2-8, 8)]} {[c for c in pcsx2.readmem(ptr2, 8)]} {pcsx2.readmem(ptr2-8, 16)}')


sys.exit(0)


Lptr = pcsx2.peek32(0x0056CBD0)
L = GCObject(pcsx2, Lptr)
print(L.getglobal('gameflow_ShouldGameStateApply'))
sys.exit(0)

ptr = pcsx2.peek32(0x00da38c0)
print(f'{ptr:08X}  PTR')
for faction,address in [('M', 0x00502052), ('C', 0x005024d4), ('K', 0x005029be)]:
  idx = pcsx2.peek16(address)
  print(f'{faction} {address:08X} {idx:4d} {[c for c in pcsx2.readmem(ptr+idx-8, 16)]}')

for row in range(30):
  print(f'{ptr+row*16:08X}  [{' '.join([c and str(c) or ' ' for c in pcsx2.readmem(ptr+row*16, 16)])}]')

sys.exit(0)

cards = [
  pcsx2.peek32(0x005240e4 + 0x28*i)
  for i in range(-2, 52+2)
]
print(cards)
sys.exit(0)

for (addr, val, expected) in [
  ('radard', pcsx2.readmem(0x004a40e8, 8), ''),
  ('0x005131e0', pcsx2.peek32(0x005131e0), 1),
  ('0x00501a44', '%x' % pcsx2.peek32(0x00501a44), 'n/a'),
  ('*0x00501a44', '%x' % pcsx2.peek32(pcsx2.peek32(0x00501a44)), 'n/a'),
  ('*0x00501a44+0x10', pcsx2.peek32(pcsx2.peek32(0x00501a44) + 0x10), 1),
  ('0x00558c8c', pcsx2.peek32(0x00558c8c), 999),
  ('0x00558c8c', pcsx2.peek32(0x00558c8c), 3000),
  ('0x00558c8c', pcsx2.peek32(0x00558c8c), 50),
  ('0x005153f0', pcsx2.peek32(0x005153f0), 1),
]:
  print(addr, expected, val)

Lptr = pcsx2.peek32(0x0056CBD0)
L = GCObject(pcsx2, Lptr)

'''
0x005131e0 1 0 ; 1 if the player has control, 0 in menus/cutscenes/loading
0x00501a44 n/a 197136c ; pointer to something; briefly a pointer to itself during loading
*0x00501a44 n/a 501a44 ; pointer back to 0x00501a44
*0x00501a44+0x10 1 0 ; not sure what this is but RA disables if it and 0x005131e0 are both 1
0x00558c8c 999 200 ; max ammo counter, RA checks for 999/3000/50 to detect infinite ammo cheats
0x00558c8c 3000 200
0x00558c8c 50 200
0x005153f0 1 0 ; invincibility flag?

When transitioning between maps, we see:
- player in control flag to 0
- 0x00501a44 points to itself
- lua state becomes ill-formed
--- begin danger zone
- lua state able to initialize again (but is corrupt)
- 0x00501a44 points to a new structure
- L is pointed to a new lua state
- player in control flag to 1
--- end danger zone

We have a window here where the lua state looks ok but trying to do anything
significant with it will crash.

Using the player-in-control flag is probably sufficient?
'''

sys.exit(0)

for ptr in [0x0054E620, 0x0054E4B0, 0x00558B4C, 0x00559634, 0x0059EB14, 0x0059EB3C, 0x007DA310, 0x00BF2524, 0x00D9B030]:
  addr = pcsx2.peek32(ptr)
  money = pcsx2.peekf32(addr + 0xB60)
  print(f'{ptr:08X} -> {addr:08X} -> {money}')

sys.exit(0)

Lptr = pcsx2.peek32(0x0056CBD0)
L = GCObject(pcsx2, Lptr)

seen = L.initialSeen()
seen[L._G.val.addr] = True

L.getglobal('util_PrintDebugMsg').dump(seen)
L.getglobal('table_Debug').dump(seen)


# util_PrintDebugMsg = L.getglobal('util_PrintDebugMsg').val
# util_PrintDebugMsg.getk(0).val.setData(b'sDebugBuffer')

# So, to put intel in the pool, we do this injection and set iTargetIntel to something
# very high, like maybe infinity or at least 200
# Then to unlock the ace we set iTargetIntel to 0
gameflow_AttemptAceMissionUnlock = L.getglobal('gameflow_AttemptAceMissionUnlock')
L.getglobal('util_PrintDebugMsg').setval(gameflow_AttemptAceMissionUnlock.val.addr)
L.getglobal('Debug_Printf').setval(gameflow_AttemptAceMissionUnlock.val.addr)
L.getglobal('iTargetIntel').setval(2.0)

sys.exit(0)


clubs = [ 0x005240e4 + i*0x28 for i in range(13) ]
diamonds = [ 0x005242ec + i*0x28 for i in range(13) ]
hearts = [ 0x005244f4 + i*0x28 for i in range(13) ]
spades = [ 0x005246fc + i*0x28 for i in range(13) ]

"""
; complete first set of contracts
N:0xX005131e0=1_I:0xX00501a44_O:0xX00000010=1O:0xX00558c8c=999O:0xX00558c8c=3000O:0xX00558c8c=50P:0xX005153f0=1.1.
S
B:1
_I:0x 00502052
_M:0xL00da38c0=3
B:1
_I:0x 00502052
_d0xL00da38c0=2
_O:0xX004a40e8=1400005746
_Q:0xX004a40e8=1634886770
_Q:0x 00502052>0
_0xX00578594=416888603
_I:0x 00502052
_Q:0xH00da38c0<=52
_I:0x 00502052
_Q:0xH00da38c0>49
S
0xX00578594=416888603
_d0xX00579468!=3
_0xX00579468=3

; complete second set of contracts
N:0xX005131e0=1_I:0xX00501a44_O:0xX00000010=1_O:0xX00558c8c=999_O:0xX00558c8c=3000_O:0xX00558c8c=50_P:0xX005153f0=1.1.
S
B:4_I:0x 00502052_M:0xL00da38c0=3
_B:4_I:0x 00502052_d0xL00da38c0=2
_I:0x 00502052_Q:0xL00da38c0>4
_I:0x 00502052_Q:0xL00da38c0<=7
_Q:0xX004a40e8=1400005746
_Q:0x 00502052>0
_0xX00578594=467221460
S
0xX00578594=467221460
_d0xX00579468!=3_0xX00579468=3

N:0xX005131e0=1_I:0xX00501a44_O:0xX00000010=1_O:0xX00558c8c=999_O:0xX00558c8c=3000_O:0xX00558c8c=50_P:0xX005153f0=1.1.
S
B:1_I:0x 00502052_M:0xL00da38c0=3
_B:1_I:0x 00502052_d0xL00da38c0=2
_Q:0xX004a40e8=1316119666
_Q:0x 00502052>0
_0xX00578594=3769370840
_I:0x 00502052_Q:0xL00da38c0<=4
S
0xX00578594=3769370840
_d0xX00579468!=3
_0xX00579468=3

N:0xX005131e0=1_I:0xX00501a44_O:0xX00000010=1_O:0xX00558c8c=999_O:0xX00558c8c=3000_O:0xX00558c8c=50_P:0xX005153f0=1.1.
S
B:4_I:0x 00502052_M:0xL00da38c0=3
_B:4_I:0x 00502052_d0xL00da38c0=2
_Q:0xX004a40e8=1316119666
_Q:0x 00502052>0
_I:0x 00502052_Q:0xL00da38c0>4
_0xX00578594=3853258935
S
0xX00578594=3853258935
_d0xX00579468!=3
_0xX00579468=3


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
"""
