import socket
import struct

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

def str_tobject(address):
  tt = pcsx2.peek32(address)
  if tt == 0:
    return 'nil'
  elif tt == 1:  # boolean
    return str(not pcsx2.peek8(address + 4) == 0)
  elif tt == 2:  # lightuserdata
    return 'pointer$%08X' % pcsx2.peek32(address + 4)
  elif tt == 3:  # number
    # n = pcsx2.peek32(address + 4)
    # return '%d ($%08X)' % (n, n)
    return pcsx2.peekf32(address + 4)
  elif tt in {4, 5, 6, 7, 8}:  # collectable objects
    return str_gcobject(pcsx2.peek32(address + 4))
  else:
    return '<<unknown:%d>>' % tt

def str_gcobject(address):
  tt = pcsx2.peek8(address + 0x04)
  if tt == 4:  # string
    hash = pcsx2.peek32(address + 8)
    size = pcsx2.peek32(address + 12)
    if size > 64:
      data = ('<<too large: %d>>' % size).encode()
    else:
      data = pcsx2.readmem(address + 16, size)
    # return 'string$%08X[size=%d,hash=%d] %s' % (address, size, hash, data)
    return '%s [h=%08X,$%08X]' % (repr(data.decode(errors='replace')), hash, address)
  elif tt == 5:  # table
    array_size = pcsx2.peek32(address + 0x1C)
    hash_size = 2 ** pcsx2.peek8(address + 0x07)
    return 'table$%08X[a=%d,h=%d]' % (address, array_size, hash_size)
  elif tt == 6:  # function
    isC = pcsx2.peek8(address + 6)
    nups = pcsx2.peek8(address + 7)
    if isC > 0:
      return 'cfunction$%08X[%d]' % (pcsx2.peek32(address + 12), nups)
    else:
      return 'function$%08X[%d]' % (address, nups)
  elif tt == 7:  # fulluserdata
    return 'fulluserdata$%08X' % address
  elif tt == 8:  # thread
    return 'thread$%08X' % address

def dump_function(address, indent='', seen=None):
  isC = pcsx2.peek8(address + 6)
  nups = pcsx2.peek8(address + 7)
  if isC:
    return
  print('%sFENV' % indent, str_tobject(address + 16))

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
    print('%sCONST$%08X' % (indent, k+i*8), str_tobject(k + i*8))

  dump_gclist(pcsx2.peek32(address + 64), indent, seen)

def dump_node(address, indent='', seen=None):
  ktype = ltypes[pcsx2.peek32(address)]
  if ktype == 'NIL':
    return
  vtype = ltypes[pcsx2.peek32(address + 8)]
  print('%s[Node$%08X] %s: %s' % (indent, address, str_tobject(address), str_tobject(address + 8)))
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
    print('%s[%4d] %s' % (indent, i, str_tobject(array + i*8)))

  for i in range(hash_size):
    dump_node(hash + i*20, indent, seen)

  if metatable > 0 and metatable != _METATABLE:
    print('%s[META] %s' % (indent, str_gcobject(metatable)))
    dump_table(metatable, indent + '  ', seen)


L = pcsx2.peek32(0x0056CBD0)
print('L is at: $%08X' % L)
peek8assert(L + 0x04, 8, 'L must be LUA_TTHREAD')
peek8assert(L + 0x40, 5, 'L->gt must be LUA_TTABLE')

stack = pcsx2.peek32(L + 0x1C)
stacksize = pcsx2.peek32(L + 0x20)
# top = pcsx2.peek32(L + 0x08)
for i in range(stacksize):
  print('[STACK$%08X]' % (stack+i*8), str_tobject(stack+i*8))

l_G = pcsx2.peek32(L + 0x10)
print('l_G is at: $%08X' % l_G)
print('_REGISTRY:', str_tobject(l_G + 0x38))
dump_table(pcsx2.peek32(l_G + 0x38 + 4), '  ')
_METATABLE = pcsx2.peek32(l_G + 0x44)
print('_METATABLE:', str_tobject(l_G + 0x40))
dump_table(pcsx2.peek32(l_G + 0x40 + 4), '  ')

_G = pcsx2.peek32(L + 0x44)
print('_G is at: $%08X' % _G)
peek8assert(_G + 0x04, 5, '_G must be LUA_TTABLE')
print('_G array size:', pcsx2.peek32(_G + 0x1C))
print('_G hash size:', 2 ** pcsx2.peek8(_G + 0x07))

print(str_gcobject(_G))
dump_table(_G, '  ')
