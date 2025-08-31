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


def dump_node(address, indent='', seen=None):
  k = TObject(pcsx2, address)
  if isinstance(k, Lua_Nil):
    # Check this before checking v, because if k is nil, v may be uninitialized
    return
  v = TObject(pcsx2, address + 8)
  print('%s[Node$%08X] %s: %s' % (indent, address, k, v))
  if isinstance(v.val, Lua_GCTable):
    dump_table(v.val.addr, indent + '  ', seen)
  if isinstance(v.val, Lua_GCFunction):
    v.dump(seen, indent + '  ')

def dump_gclist(address, indent='', seen=None):
  return
  while address != 0:
    print('%s[GC] %s' % (indent, str_gcobject(address)))
    address = pcsx2.peek32(address)


_METATABLE = None
def dump_table(address, indent='', seen=None):
  seen = seen or set()
  if address in seen:
    return
  seen.add(address)

  metatable = pcsx2.peek32(address + 0x08)
  array = pcsx2.peek32(address + 0x0C)
  array_size = pcsx2.peek32(address + 0x1C)
  hash = pcsx2.peek32(address + 0x10)
  hash_size = 2 ** pcsx2.peek8(address + 0x07)

  for i in range(array_size):
    print('%s[%4d] %s' % (indent, i, TObject(pcsx2, array + i*8)))

  for i in range(hash_size):
    dump_node(hash + i*20, indent, seen)

  if metatable > 0 and metatable != _METATABLE:
    metatable = TObject(pcsx2, metatable)
    if not isinstance(metatable, Lua_Nil):
      print('%s[META] %s' % (indent, TObject(pcsx2, metatable)))
      dump_table(metatable, indent + '  ', seen)


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
