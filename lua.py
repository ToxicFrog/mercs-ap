from lopcode import LuaOpcode

_CACHE = {}

LUA_TNIL = 0
LUA_TBOOL = 1
LUA_TPOINTER = 2
LUA_TNUMBER = 3
LUA_TSTRING = 4
LUA_TTABLE = 5
LUA_TFUNCTION = 6
LUA_TUSERDATA = 7
LUA_TTHREAD = 8

class Lua_TObject:
  def __init__(self, pine, addr):
    _CACHE[addr] = self
    self.addr = addr
    self.tt = pine.peek32(addr)
    self.val = pine.peek32(addr+4)

  def __str__(self):
    return str(self.val)

  def __eq__(self, other):
    return self.addr == other.addr

  def dump(self, seen, indent=''):
    return

class Lua_Nil(Lua_TObject):
  def __str__(self):
    return 'nil'

class Lua_Bool(Lua_TObject):
  def __str__(self):
    return str(self.val != 0)

class Lua_Pointer(Lua_TObject):
  def __str__(self):
    return 'pointer$%08X' % self.val

class Lua_Number(Lua_TObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.val = pine.peekf32(addr+4)

class Lua_TObjectGC(Lua_TObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    gcaddr = self.val
    self.val = GCObject(pine, gcaddr)
    if self.val is None:
      self.val = Lua_CorruptGCObject(gcaddr, None)
    elif self.tt != self.val.tt:
      self.val = Lua_CorruptGCObject(gcaddr, self.val.tt)

  def dump(self, seen, indent=''):
    return self.val.dump(seen, indent)

class Lua_CorruptGCObject:
  def __init__(self, addr, tt):
    self.addr = addr
    self.tt = tt

  def __str__(self):
    return f'<<corrupt gcobject${self.addr:08X} tt={self.tt}'

  def dump(self, seen, indent=''):
    return

class Lua_GCObject:
  def __init__(self, pine, addr):
    _CACHE[addr] = self
    self.addr = addr
    self.next = pine.peek32(addr)
    self.tt = pine.peek8(addr+4)

  def dump(*args):
    raise NotImplementedError

class Lua_GCString(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.hash = pine.peek32(addr+8)
    self.size = pine.peek32(addr+12)
    self.data = pine.readmem(addr+16, self.size)

  def __str__(self):
    return '%s [h=%08X,$%08X]' % (repr(self.data.decode(errors='replace')), self.hash, self.addr)

  def dump(*args):
    return

class Lua_GCTable(Lua_GCObject):
  class Node:
    def __init__(self, pine, addr):
      self.addr = addr
      try:
        self.k = TObject(pine, addr)
      except:
        self.k = None
        self.v = None
        return
      if self.k is None or isinstance(self.k, Lua_Nil):
        self.v = None
        self.next = None
        return
      self.v = TObject(pine, addr+8)
      self.next = pine.peek32(addr+16)

    def dump(self, seen, indent=''):
      if self.k is None or self.v is None:
        return
      print('%s[Node$%08X] %s: %s' % (indent, self.addr, self.k, self.v))
      self.k.dump(seen, indent + 'K ')
      self.v.dump(seen, indent + '  ')

  def __init__(self, pine, addr):
    super().__init__(pine, addr)

    mt_ptr = pine.peek32(addr + 0x08)
    if mt_ptr > 0:
      self.metatable = GCObject(pine, mt_ptr)
    else:
      self.metadata = None


    self.array_size = pine.peek32(addr + 0x1C)
    self.array_ptr = pine.peek32(addr + 0x0C)
    self.array = [
      TObject(pine, self.array_ptr + i*8)
      for i in range(self.array_size)
    ]

    self.hash_size = 2 ** pine.peek8(addr + 0x07)
    self.hash_ptr = pine.peek32(addr + 0x10)

    self.hash = [
      self.Node(pine, self.hash_ptr + i*20)
      for i in range(self.hash_size)
    ]

  def __str__(self):
    return 'table$%08X[a=%d,h=%d]' % (self.addr, self.array_size, self.hash_size)

  def hasMetatable(self, seen):
    return (
      self.metatable is not None
      and self.metatable.tt != 0
      and self.metatable.addr != seen['_METATABLE'])

  def dump(self, seen, indent=''):
    if self.addr in seen:
      return
    seen[self.addr] = self

    for i,v in enumerate(self.array):
      if v is None or v.tt == LUA_TNIL:
        continue
      print(f'{indent}[{i}:${self.array_ptr+i*8:08X}] {v}')
      v.dump(seen, indent + '  ')

    for node in self.hash:
      if node.k is None or node.k.tt == LUA_TNIL:
        continue
      node.dump(seen, indent)

    if self.hasMetatable(seen):
      print(f'{indent}META: {self.metatable}')
      self.metatable.dump(seen, indent + '  ')


class Lua_GCFunction(Lua_GCObject):
  class Proto:
    def __init__(self, pine, addr):
      self.addr = addr
      self.k = pine.peek32(addr + 8)
      self.sizek = pine.peek32(addr + 40)
      self.klist = [
        TObject(pine, self.k + i*8)
        for i in range(self.sizek)
      ]
      self.sizecode = pine.peek32(addr + 44)
      self.codeptr = pine.peek32(addr + 12)
      self.code = [
        LuaOpcode(pine.peek32(self.codeptr + i*4))
        for i in range(self.sizecode)
      ]

  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.isC = pine.peek8(addr + 6) != 0
    self.nups = pine.peek8(addr + 7)
    if self.isC:
      self.cfunction = pine.peek32(addr + 12)
      self.fenv = None
    else:
      self.proto = self.Proto(pine, pine.peek32(addr + 12))
      self.fenv = TObject(pine, addr + 16)

  def __str__(self):
    if self.isC:
      return 'cfunction$%08X[%d]' % (self.cfunction, self.nups)
    else:
      return 'function$%08X[%d]' % (self.addr, self.nups)

  def dump(self, seen, indent=''):
    if self.isC:
      return
    if self.addr in seen:
      return
    seen[self.addr] = self

    # print(f'{indent}PROTO${self.proto.addr:08X}')
    if self.fenv.val.addr != seen['_G']:
      print(f'{indent}FENV: {self.fenv}')
      self.fenv.dump(seen, indent + '  ')
    for i in range(self.proto.sizek):
      print(f'{indent}CONST${self.proto.k + i*8:08X} {self.proto.klist[i]}')

    print(f'{indent}CODE ${self.proto.codeptr:08X}')
    for i,op in enumerate(self.proto.code):
      print(f'{indent}  {i:4d} {op.op:08X} {op.pprint(self.proto, i)}')

    # they all seem to be nil
    # upvs = pcsx2.peek32(address + 20)
    # for i in range(nups):
    #   upv = pcsx2.peek32(upvs + i*4)
    #   obj = pcsx2.peek32(upv + 8)
    #   print('%sUPVAL %s' % (indent, str_tobject(obj)))
    # dump_gclist(pcsx2.peek32(address + 64), indent, seen)


class Lua_GCUserdata(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.metatable = Lua_GCTable(pine.peek32(addr+8))
    self.size = pine.peek32(addr+12)
    # self.data = pine.readmem(addr+16, self.size)

  def __str__(self):
    return 'userdata$%08X[size=%d,mt=%s]' % (self.addr, self.size, self.metatable)

  def dump(self, seen, indent = ''):
    # Don't know any internal structure to dump
    # Maybe dump the first 64 bytes someday or something
    return

class Lua_GCThread(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    print(f'Loading lua_State${addr:08X}')

    self.stackbase = pine.peek32(addr + 0x1C)
    self.stacksize = pine.peek32(addr + 0x20)
    self.stacktop = pine.peek32(addr + 0x08)
    self.stack = [
      TObject(pine, self.stackbase + i*8)
      for i in range((self.stacktop - self.stackbase)//8)
    ]
    print(f'- stack: {self.stackbase:08X}..{self.stacktop:08X} (capacity: {self.stacksize})')

    # TODO: read stack into list of TObject
    # global state shared across threads, like the string table
    # TODO: implement actual class for this with default_metatable and registry fields
    self.l_G = pine.peek32(addr + 0x10)
    print(f'- shared global state: ${self.l_G:08X}')
    self._G = TObject(pine, addr + 0x40)
    print(f'- globals: {self._G}')
    self._REGISTRY = TObject(pine, self.l_G + 0x38)
    print(f'- registry: {self._REGISTRY}')
    self._METATABLE = TObject(pine, self.l_G + 0x40)
    print(f'- default metatable: {self._METATABLE}')

  def __str__(self):
    return 'thread$%08X' % self.addr

  def dump(self, seen, indent=''):
    seen['_METATABLE'] = self._METATABLE.val.addr
    seen['_G'] = self._G.val.addr

    print(f'{indent}STACK:')
    for obj in self.stack:
      print(f'{indent}- {obj}')
      obj.dump(seen, indent + '    ')

    print(f'{indent}_METATABLE: {self._METATABLE}')
    self._METATABLE.dump(seen, indent + '  ')

    print(f'{indent}_REGISTRY: {self._REGISTRY}')
    self._REGISTRY.dump(seen, indent + '  ')

    print(f'{indent}_G: {self._G}')
    self._G.dump(seen, indent + '  ')


# Implementations of TObject
LUA_TYPES = [
  Lua_Nil, Lua_Bool, Lua_Pointer, Lua_Number,
  # string, table, function, fulluserdata, thread
  Lua_TObjectGC, Lua_TObjectGC, Lua_TObjectGC, Lua_TObjectGC, Lua_TObjectGC
]

# Implementations of GCObject
LUA_GCTYPES = [
  None, None, None, None,
  Lua_GCString, Lua_GCTable, Lua_GCFunction, Lua_GCUserdata, Lua_GCThread
]


def TObject(pine, addr):
  if addr in _CACHE:
    return _CACHE[addr]
  tt = pine.peek32(addr)
  if tt == 0xFFFFFFFF:
    # Removed by garbage collector
    return None
  # print('creating tobject', f'{addr:08X} {tt} {pine.peek32(addr+4):08X}')
  assert tt < len(LUA_TYPES), f'Unknown type {tt} constructing TObject${addr:08X}'
  return LUA_TYPES[tt](pine, addr)

def GCObject(pine, addr):
  if addr in _CACHE:
    return _CACHE[addr]
  tt = pine.peek8(addr+4)
  if tt == 0xFFFFFFFF:
    # Removed by garbage collector
    return None
  # print('creating gcobject', f'{addr:08X} {tt}')
  assert tt < len(LUA_GCTYPES), f'Unknown type {tt} constructing GCObject${addr:08X}'
  if LUA_GCTYPES[tt] is None:
    # wtf??
    return None
  assert LUA_GCTYPES[tt] is not None, f'Attempting to create gcobject${addr:08X} from primitive type {tt}'
  return LUA_GCTYPES[tt](pine, addr)
