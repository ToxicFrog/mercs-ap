import socket
import struct

from lua import TObject, GCObject
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


def dump_function(address, indent='', seen=None):
  isC = pcsx2.peek8(address + 6)
  nups = pcsx2.peek8(address + 7)
  if isC:
    return

  fenv = TObject(pcsx2, address + 16)
  print('%sFENV' % indent, fenv)

  # they all seem to be nil
  # upvs = pcsx2.peek32(address + 20)
  # for i in range(nups):
  #   upv = pcsx2.peek32(upvs + i*4)
  #   obj = pcsx2.peek32(upv + 8)
  #   print('%sUPVAL %s' % (indent, str_tobject(obj)))

  # todo: upvalues
  proto = pcsx2.peek32(address + 12)
  # constants at +8, locals at +24, upvalues at +28
  # print('%sSOURCE' % indent, str_gcobject(proto + 32))
  k = pcsx2.peek32(proto + 8)
  sizek = pcsx2.peek32(proto + 40)
  for i in range(sizek):
    print('%sCONST$%08X' % (indent, k+i*8), TObject(pcsx2, k + i*8))

  dump_gclist(pcsx2.peek32(address + 64), indent, seen)

def dump_node(address, indent='', seen=None):
  ktype = ltypes[pcsx2.peek32(address)]
  if ktype == 'NIL':
    return
  vtype = ltypes[pcsx2.peek32(address + 8)]
  print('%s[Node$%08X] %s: %s' % (indent, address, TObject(pcsx2, address), TObject(pcsx2, address + 8)))
  if vtype == 'TABLE':
    dump_table(pcsx2.peek32(address + 12), indent + '  ', seen)
  if vtype == 'FUNCTION':
    dump_function(pcsx2.peek32(address + 12), indent + '  ', seen)
  # next = pcsx2.peek32(address + 16)
  # if next > 0:
  #   dump_node(next, indent)

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
