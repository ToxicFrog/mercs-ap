

class Lua_TObject:
  def __init__(self, pine, addr):
    self.addr = addr
    self.tt = pine.peek32(addr)
    self.val = pine.peek32(addr+4)

  def __str__(self):
    return str(self.val)

  def __eq__(self, other):
    return self.addr == other.addr

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

  def __str__(self):
    if self.isC:
      return 'cfunction$%08X[%d]' % (self.cfunction, self.nups)
    else:
      return 'function$%08X[%d]' % (self.addr, self.nups)

class Lua_GCUserdata(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.metatable = Lua_GCTable(pine.peek32(addr+8))
    self.size = pine.peek32(addr+12)
    # self.data = pine.readmem(addr+16, self.size)

  def __str__(self):
    return 'userdata$%08X[size=%d,mt=%s]' % (self.addr, self.size, self.metatable)

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


def TObject(pine, addr):
  tt = pine.peek32(addr)
  return LUA_TYPES[tt](pine, addr)

def GCObject(pine, addr):
  tt = pine.peek8(addr+4)
  return LUA_GCTYPES[tt](pine, addr)
