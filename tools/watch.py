import sys
import time

from .pine import Pine
from .lua import GCObject, TObject

pcsx2: Pine = Pine(path = '/run/user/8509/pcsx2.sock')

print(pcsx2.game_info())

# from .stats import PDAStats
from .data.statsdata import VEHICLE_NAMES, VEHICLES_DESTROYED_ADDR

# This has structure:
# uint32 nrof_vehicles
# uint32 nrof_driven
# float* array_start ?? seems to point to idx 1
# float* array_end
# then at array_start we have a float[nrof_vehicles] where >0 is the distance
# traveled in it. There is an entry for "on foot".
DRIVE_ADDR = 0x005A6A40
DRIVE_ARRAY = pcsx2.peek32(DRIVE_ADDR+8) - 4

for idx,name in enumerate(VEHICLE_NAMES):
  n = pcsx2.peekf32(VEHICLES_DESTROYED_ADDR + idx*4)
  dist = pcsx2.peekf32(DRIVE_ARRAY + idx*4)
  if 'unknown' in name:
    hilight = '\x1B[1;31m'
  elif '?' in name:
    hilight = '\x1B[1;36m'
  else:
    hilight = ''
  if n > 0 or dist > 0:
    print(f'{hilight}{idx:4d} {name:20s} {int(n):4d} {dist:.0f}m\x1B[0m')

def readCollectableCount(addr):
  idx = pcsx2.peek16(addr)
  if idx == 0:
    return ''
  ptr = 0xda38c0 + idx
  buf = pcsx2.readmem(ptr, 8)
  return buf[:buf.find(0)].decode(errors='replace')

for label,base in [
  ('LP', 0x50202a),
  ('BP', 0x502be0),
  ('PM', 0x502202),
  ('NT', 0x502294),
]:
  print(f'{label} ${base:08X} {[readCollectableCount(base+i*2) for i in range(-8,16)]}')
  # print('indexes', [pcsx2.peek16(base+i*2) for i in range(8)])
  # print('pointers', ['%08X' % pcsx2.peek32(0xda38c0 + pcsx2.peek16(base+i*2)) for i in range(8)])

sys.exit(0)
