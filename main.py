import socket
import struct

def pine_send(sock: socket.socket, opcode: int, payload: bytes = b''):
  size = len(payload) + 5
  data = struct.pack('< I B %ds' % len(payload), size, opcode, payload)
  # print('>>', size, opcode, data)
  sock.send(data)

def pine_recv(sock, format=None):
  header = sock.recv(5)
  (size, result) = struct.unpack('< I B', header)
  assert result == 0, 'Error from emulator: result=%d' % result

  if size > 5:
    data = sock.recv(size-5)
  else:
    data = b''

  # print('<<', size, result, header, data)

  if format:
    return struct.unpack(format, data)
  else:
    return (data,)

def pine_recvstring(sock):
  data = pine_recv(sock)[0]
  size = struct.unpack('< I', data[0:4])[0]
  assert len(data) == size+4, 'String consistency error, size=%d len(data)=%d' % (size, len(data))
  return data[4:-1]

def getinfo(sock, opcode, title):
  pine_send(sock, opcode, b'')
  result = pine_recvstring(sock)
  print(title, result)

ltypes = [
  'NIL', 'BOOLEAN', 'POINTER', 'NUMBER', 'STRING', 'TABLE', 'FUNCTION', 'USERDATA', 'THREAD'
]

print('Opening socket...')
sock = socket.socket(family = socket.AF_UNIX, type = socket.SOCK_STREAM)
sock.connect('/run/user/8509/pcsx2.sock')

getinfo(sock, 0x0B, 'Title:')
getinfo(sock, 0x0C, 'ID:')
getinfo(sock, 0x0D, 'UUID:')
getinfo(sock, 0x0E, 'Version:')


def peek4(addr):
  pine_send(sock, 0x02, struct.pack('< I', addr))
  return pine_recv(sock, '< I')[0]

def peek4f(addr):
  pine_send(sock, 0x02, struct.pack('< I', addr))
  return pine_recv(sock, '< f')[0]

def peek1(addr):
  pine_send(sock, 0x00, struct.pack('< I', addr))
  return pine_recv(sock, '< B')[0]

def peek1assert(addr, val, reason):
  mem = peek1(addr)
  assert mem == val, '%s: expected %d, got %d' % (reason, val, mem)
  print('[OK]', reason)

def readmem(address, size):
  buf = b''
  while size >= 8:
    pine_send(sock, 0x03, struct.pack('< I', address))
    buf = buf + pine_recv(sock, '8s')[0]
    address += 8
    size -= 8
  while size > 0:
    pine_send(sock, 0x00, struct.pack('< I', address))
    buf = buf + pine_recv(sock, '1s')[0]
    address += 1
    size -= 1
  return buf

def str_tobject(address):
  tt = peek4(address)
  if tt == 0:
    return 'nil'
  elif tt == 1:  # boolean
    return str(not peek1(address + 4) == 0)
  elif tt == 2:  # lightuserdata
    return 'pointer$%08X' % peek4(address + 4)
  elif tt == 3:  # number
    # n = peek4(address + 4)
    # return '%d ($%08X)' % (n, n)
    return peek4f(address + 4)
  elif tt in {4, 5, 6, 7, 8}:  # collectable objects
    return str_gcobject(peek4(address + 4))
  else:
    return '<<unknown:%d>>' % tt

def str_gcobject(address):
  tt = peek1(address + 0x04)
  if tt == 4:  # string
    hash = peek4(address + 8)
    size = peek4(address + 12)
    if size > 64:
      data = ('<<too large: %d>>' % size).encode()
    else:
      data = readmem(address + 16, size)
    # return 'string$%08X[size=%d,hash=%d] %s' % (address, size, hash, data)
    return '%s [h=%08X,$%08X]' % (repr(data.decode(errors='replace')), hash, address)
  elif tt == 5:  # table
    array_size = peek4(address + 0x1C)
    hash_size = 2 ** peek1(address + 0x07)
    return 'table$%08X[a=%d,h=%d]' % (address, array_size, hash_size)
  elif tt == 6:  # function
    isC = peek1(address + 6)
    nups = peek1(address + 7)
    if isC > 0:
      return 'cfunction$%08X[%d]' % (peek4(address + 12), nups)
    else:
      return 'function$%08X[%d]' % (address, nups)
  elif tt == 7:  # fulluserdata
    return 'fulluserdata$%08X' % address
  elif tt == 8:  # thread
    return 'thread$%08X' % address

def dump_function(address, indent='', seen=None):
  isC = peek1(address + 6)
  nups = peek1(address + 7)
  if isC:
    return
  print('%sFENV' % indent, str_tobject(address + 16))

  # they all seem to be nil
  # upvs = peek4(address + 20)
  # for i in range(nups):
  #   upv = peek4(upvs + i*4)
  #   obj = peek4(upv + 8)
  #   print('%sUPVAL %s' % (indent, str_tobject(obj)))

  # todo: upvalues
  proto = peek4(address + 12)
  # constants at +8, locals at +24, upvalues at +28
  # print('%sSOURCE' % indent, str_gcobject(proto + 32))
  k = peek4(proto + 8)
  sizek = peek4(proto + 40)
  for i in range(sizek):
    print('%sCONST' % indent, str_tobject(k + i*8))

def dump_node(address, indent='', seen=None):
  ktype = ltypes[peek4(address)]
  if ktype == 'NIL':
    return
  vtype = ltypes[peek4(address + 8)]
  print('%s[Node$%08X] %s: %s' % (indent, address, str_tobject(address), str_tobject(address + 8)))
  if vtype == 'TABLE':
    dump_table(peek4(address + 12), indent + '  ', seen)
  if vtype == 'FUNCTION':
    dump_function(peek4(address + 12), indent + '  ', seen)
  # next = peek4(address + 16)
  # if next > 0:
  #   dump_node(next, indent)

_METATABLE = None
def dump_table(address, indent='', seen=None):
  seen = seen or set()
  if address in seen:
    return
  seen.add(address)

  metatable = peek4(address + 0x08)
  array = peek4(address + 0x0C)
  array_size = peek4(address + 0x1C)
  hash = peek4(address + 0x10)
  hash_size = 2 ** peek1(address + 0x07)

  for i in range(array_size):
    print('%s[%4d] %s' % (indent, i, str_tobject(array + i*8)))

  for i in range(hash_size):
    dump_node(hash + i*20, indent, seen)

  if metatable > 0 and metatable != _METATABLE:
    print('%s[META] %s' % (indent, str_gcobject(metatable)))
    dump_table(metatable, indent + '  ', seen)


L = peek4(0x0056CBD0)
print('L is at: $%08X' % L)
peek1assert(L + 0x04, 8, 'L must be LUA_TTHREAD')
peek1assert(L + 0x40, 5, 'L->gt must be LUA_TTABLE')

l_G = peek4(L + 0x10)
print('l_G is at: $%08X' % l_G)
print('_REGISTRY:', str_tobject(l_G + 0x38))
dump_table(peek4(l_G + 0x38 + 4), '  ')
_METATABLE = peek4(l_G + 0x44)
print('_METATABLE:', str_tobject(l_G + 0x40))
dump_table(peek4(l_G + 0x40 + 4), '  ')

_G = peek4(L + 0x44)
print('_G is at: $%08X' % _G)
peek1assert(_G + 0x04, 5, '_G must be LUA_TTABLE')
print('_G array size:', peek4(_G + 0x1C))
print('_G hash size:', 2 ** peek1(_G + 0x07))

print(str_gcobject(_G))
dump_table(_G, '  ')
