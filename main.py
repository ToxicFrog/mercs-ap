import socket
import struct

from lua import TObject, GCObject, Lua_Nil, Lua_GCFunction, Lua_GCTable
from pine import Pine

pcsx2: Pine = Pine(path = '/run/user/8509/pcsx2.sock')

print(pcsx2.game_info())

ltypes = [
  'NIL', 'BOOLEAN', 'POINTER', 'NUMBER', 'STRING', 'TABLE', 'FUNCTION', 'USERDATA', 'THREAD'
]

def peek8assert(addr, val, reason):
  mem = pcsx2.peek8(addr)
  assert mem == val, '%s: expected %d, got %d' % (reason, val, mem)
  print('[OK]', reason)


Lptr = pcsx2.peek32(0x0056CBD0)
print(f'L is at: {Lptr:08X}')

L = GCObject(pcsx2, Lptr)
assert L.tt == 8, 'L must be LUA_TTHREAD'
assert L._G.tt == 5, 'L->gt must be LUA_TTABLE'

seen = set()
L.dump(seen, '')
