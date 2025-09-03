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
