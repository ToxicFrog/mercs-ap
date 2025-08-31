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
L = GCObject(pcsx2, Lptr)

print('L is at: $%08X' % L.addr)
assert L.tt == 8, 'L must be LUA_TTHREAD'
assert L._G.tt == 5, 'L->gt must be LUA_TTABLE'

# for i in range(L.stacksize):
#   print('[STACK$%08X]' % (L.stack+i*8), TObject(L.stack+i*8))

print('l_G is at: $%08X' % L.l_G)
registry = TObject(pcsx2, L.l_G + 0x38)
print('_REGISTRY:', registry)
dump_table(registry.val.addr, '  ')
metatable = TObject(pcsx2, L.l_G + 0x40)
print('_METATABLE:', metatable)
dump_table(metatable.val.addr, '  ')

print('_G is at: $%08X' % L._G.val.addr)
print(L._G.val)
dump_table(L._G.val.addr, '  ')
