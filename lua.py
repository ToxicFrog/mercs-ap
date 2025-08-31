

class Lua_TObject:
  def __init__(self, pine, addr):
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
    self.addr = addr
    self.tt = pine.peek32(addr)
    self.val = pine.peekf32(addr+4)

class Lua_TObjectGC(Lua_TObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.val = LUA_GCTYPES[self.tt](pine, self.val)
    assert self.tt == self.val.tt

  def dump(self, seen, indent=''):
    return self.val.dump(seen, indent)

class Lua_GCObject:
  def __init__(self, pine, addr):
    self.addr = addr
    self.next = pine.peek32(addr)
    self.tt = pine.peek8(addr+4)

class Lua_GCString(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.hash = pine.peek32(addr+8)
    self.size = pine.peek32(addr+12)
    self.data = pine.readmem(addr+16, self.size)

  def __str__(self):
    return '%s [h=%08X,$%08X]' % (repr(self.data.decode(errors='replace')), self.hash, self.addr)

class Lua_GCTable(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.array_size = pine.peek32(addr + 0x1C)
    self.hash_size = 2 ** pine.peek8(addr + 0x07)

  def __str__(self):
    return 'table$%08X[a=%d,h=%d]' % (self.addr, self.array_size, self.hash_size)

class Lua_GCFunction(Lua_GCObject):
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
    seen.add(self.addr)

    # print(f'{indent}PROTO${self.proto.addr:08X}')
    print(f'{indent}FENV: {self.fenv}')
    # self.fenv.dump(seen, indent + '  ')
    for i in range(self.proto.sizek):
      print(f'{indent}CONST${self.proto.k + i*8:08X} {self.proto.klist[i]}')
      # print(indent, 'CONST', i, self.proto.k + i*8)

    # they all seem to be nil
    # upvs = pcsx2.peek32(address + 20)
    # for i in range(nups):
    #   upv = pcsx2.peek32(upvs + i*4)
    #   obj = pcsx2.peek32(upv + 8)
    #   print('%sUPVAL %s' % (indent, str_tobject(obj)))
    # dump_gclist(pcsx2.peek32(address + 64), indent, seen)

  class Proto:
    def __init__(self, pine, addr):
      self.addr = addr
      self.k = pine.peek32(addr + 8)
      self.sizek = pine.peek32(addr + 40)
      self.klist = [
        TObject(pine, self.k + i*8)
        for i in range(self.sizek)
      ]


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
    self.stack = pine.peek32(addr + 0x1C)
    self.stacksize = pine.peek32(addr + 0x20)
    self.top = pine.peek32(addr + 0x08)
    # TODO: read stack into list of TObject
    # global state shared across threads, like the string table
    # TODO: implement actual class for this with default_metatable and registry fields
    self.l_G = pine.peek32(addr + 0x10)
    self._G = TObject(pine, addr + 0x40)

  def __str__(self):
    return 'thread$%08X' % self.addr

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


_CACHE = {}

def TObject(pine, addr):
  if addr not in _CACHE:
    tt = pine.peek32(addr)
    # print('%x' % addr, tt)
    assert tt < len(LUA_TYPES), f'Unknown type {tt} constructing TObject${addr:08X}'
    _CACHE[addr] = LUA_TYPES[tt](pine, addr)
  return _CACHE[addr]

def GCObject(pine, addr):
  if addr not in _CACHE:
    tt = pine.peek8(addr+4)
    # print('%x' % addr, tt)
    assert tt < len(LUA_GCTYPES), f'Unknown type {tt} constructing GCObject${addr:08X}'
    _CACHE[addr] = LUA_GCTYPES[tt](pine, addr)
  return _CACHE[addr]
