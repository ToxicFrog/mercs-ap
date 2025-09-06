'''
Lua inspection library.

To use it, initialize a PINE connector, then create Lua objects with:
  TObject(pine, address)
  GCObject(pine, address)

TObject is one type, representing mutable tag-value pairs. To query it:
  to = TObject(pine, addr)
  to.addr      # get the base address
  to.tt()      # get the tag
  to.val()     # get the value
  to.valid()   # check if it references a valid TObject in memory
  to.valid(tt) # check if it's a valid TObject with the given type

To mutate it, you have a few options:
  # Set the value and optionally the type. Can pass a primitive, another TObject,
  # or a GCObject. Throws if val doesn't match the current type (or the new type,
  # if you specify tt=).
  to.set(val)
  to.set(val, tt=T)

  # Copy the type and value from another TObject.
  to.copy(other_to)

  # Directly set the underlying memory to the given int32 values.
  to.rawset(tt, val)

GCObject is a supertype of the various garbage-collectible lua types: strings,
tables, functions, fulluserdata, and threads. The API is currently being redesigned
for better performance and consistency with TObject.
'''
from typing import Any

from .pine import Pine
from .util import MemVarInt, MemVarOpcode

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
LUA_EMPTY = 0xFFFFFFFF # Used for TObjects that have been deleted by the garbage collector

def tt_to_name(tt):
  match tt:
    case 0: return 'nil'
    case 1: return 'bool'
    case 2: return 'pointer'
    case 3: return 'number'
    case 4: return 'string'
    case 5: return 'table'
    case 6: return 'function'
    case 7: return 'userdata'
    case 8: return 'thread'
    case 0xFFFFFFFF: return '<<deleted>>'
    case _: return f'unknown:{tt}'

class LuaTypeError(RuntimeError):
  pass

# TODO: rewrite all of this to use MemVars, have a more consistent API across
# types, allow mutating between types in place, etc
class Lua_TObject:
  pine: Pine
  addr: int
  _tt: MemVarInt

  def __init__(self, pine, addr):
    _CACHE[addr] = self
    self.pine = pine
    self.addr = addr
    self._tt = MemVarInt(self.pine, self.addr)

  def __repr__(self):
    return f'TObject${self.addr:08X}<{tt_to_name(self.tt())}>({self.val()})'

  def __str__(self):
    if not self.valid():
      return f'<<invalid TObject${self.addr:08X}>>'
    return f'TObject({str(self.val())})'

  def __eq__(self, other):
    return self.addr == other.addr

  def valid(self, expected=None):
    '''
    Check if this is a valid TObject of the expected type.
    If expected=None, just checks that it's any known type.
    '''
    tt = self._tt()
    expected = tt if expected is None else expected
    if tt != expected or tt > 8:
      return False
    if tt >= 4:
      # Consistency check with enclosed GCObject
      return self.val().valid(tt)
    return True

  def tt(self):
    return self._tt()

  def val(self):
    '''
    Returns the contents of the value slot. This is either a primitive or a GCObject.
    Maps nil to None; throws on error.
    '''
    vaddr = self.addr+4
    match self.tt():
      case 0: return None
      case 1: return self.pine.peek32(vaddr) > 0
      case 2: return self.pine.peek32(vaddr)
      case 3: return self.pine.peekf32(vaddr)
      case 4|5|6|7|8: return GCObject(self.pine, self.pine.peek32(vaddr))

    raise LuaTypeError(f'Unknown tt={self.tt()} decoding TObject${self.addr:08X}')

  def dump(self, seen, indent=''):
    match self.tt():
      case 4|5|6|7|8:
        return self.val().dump(seen, indent)
      case 0|1|2|3:
        return

  def set(self, val: Any, tt: int = None):
    '''
    Set the value slot from val. If val is a GCObject, sets the value slot to
    a pointer to it.
    Throws if the val does not match the current type. To change the type as
    well, include the tt= argument.
    '''
    vaddr = self.addr+4
    if tt is None:
      tt = self.tt()
    else:
      self._tt(tt)

    match tt:
      case 0:
        assert val is None
        self.pine.poke32(vaddr, 0)
      case 1:
        assert type(val) is bool
        self.pine.poke32(vaddr, 1 if val else 0)
      case 2:
        assert type(val) is int
        self.pine.poke32(vaddr, val)
      case 3:
        assert type(val) is int or type(val) is float
        self.pine.pokef32(vaddr, val)
      case 4|5|6|7|8:
        if type(val) is Lua_TObject:
          return self.set(val.val())
        assert isinstance(val, Lua_GCObject)
        assert val.tt == tt, f"Can't set {repr(self)} to value of type {tt_to_name(val.tt)}"
        self.pine.poke32(vaddr, val.addr)
      case _:
        raise LuaTypeError(f'Invalid type {tt} in TObject.set({val})')

  def copy(self, other):
    '''
    Set our type and value from another TObject.
    To set to a reference to a GCObject, use set().
    '''
    assert type(other) is Lua_TObject
    self.rawset(other.tt(), self.pine.peek32(other.addr+4))

  def rawset(self, tt: int, n: int):
    '''
    Set the type and value slots directly with no error checking.
    '''
    self._tt(tt)
    self.pine.poke32(n)

class Lua_CorruptGCObject:
  def __init__(self, addr, tt):
    self.addr = addr
    self.tt = tt

  def __str__(self):
    return f'<<corrupt gcobject${self.addr:08X} tt={self.tt}'

  def dump(self, seen, indent=''):
    return

  def valid(self):
    return False

class Lua_GCObject:
  def __init__(self, pine, addr):
    _CACHE[addr] = self
    self.pine = pine
    self.addr = addr
    self.next = pine.peek32(addr)
    self.tt = pine.peek8(addr+4)

  def valid(self, expected):
    if expected is not None:
      return self.tt == expected
    else:
      return self.tt >= 4 and self.tt <= 8

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

  def setData(self, data):
    self.pine.writemem(self.addr+16, data)

  def dump(*args):
    return

class Lua_GCTable(Lua_GCObject):
  class Node:
    def __init__(self, pine, addr):
      self.pine = pine
      self.addr = addr
      self.next = pine.peek32(addr+16)
      self.k = TObject(self.pine, self.addr)
      self.v = TObject(self.pine, self.addr+8)

    def valid(self):
      return self.v.valid() and self.k.valid()

    def keyEq(self, k):
      '''
      Test if the key of this Node equals the given k.
      At the moment we only support string keys.
      '''
      if not self.k.valid():
        return False
      if self.k.tt() != LUA_TSTRING:
        return False

      assert type(k) is bytes
      return k == self.k.val().data

    def dump(self, seen, indent=''):
      if not self.k.valid() or self.k.tt() == LUA_TNIL:
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
    self.hash_size = 2 ** pine.peek8(addr + 0x07)
    self.hash_ptr = pine.peek32(addr + 0x10)
    self.array = [
      TObject(self.pine, self.array_ptr + i*8)
      for i in range(self.array_size)
    ]

    self.hash = [
      self.Node(self.pine, self.hash_ptr + i*20)
      for i in range(self.hash_size)
    ]

  def __str__(self):
    return 'table$%08X[a=%d,h=%d]' % (self.addr, self.array_size, self.hash_size)

  def getnode(self, key) -> Node:
    '''
    Returns the Node representing a given hash table entry.
    '''
    if type(key) == str:
      key = key.encode()
    for node in self.hash:
      if node.keyEq(key) and node.v.valid():
        return node
    return None

  def getfield(self, key) -> Lua_TObject:
    '''
    Returns a TObject for the given table entry. key can be an int or a string.
    '''
    if type(key) == int and key < self.array_size:
      return self.array[key]
    node = self.getnode(key)
    return node.v if node else None

  def hasMetatable(self, seen):
    return (
      self.metatable is not None
      and self.metatable.tt != LUA_TNIL
      and self.metatable.addr != seen.get('_METATABLE', None))

  def dump(self, seen, indent=''):
    if self.addr in seen:
      return
    seen[self.addr] = self

    for i,v in enumerate(self.array):
      if not v.valid() or v.tt() == LUA_TNIL:
        continue
      print(f'{indent}[{i}:${self.array_ptr+i*8:08X}] {v}')
      v.dump(seen, indent + '  ')

    for node in self.hash:
      if not node.valid() or node.k.tt() == LUA_TNIL:
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
        MemVarOpcode(pine, self.codeptr + i*4)
        for i in range(self.sizecode)
      ]

  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    self.name = None
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
      return f'cfunction${self.cfunction:08X}{self.nups and f'[{self.nups}]' or ''}{self.name and f' {self.name}' or ''}'
    else:
      return f'function${self.addr:08X}{self.nups and f'[{self.nups}]' or ''}{self.name and f' {self.name}' or ''}'

  def getk(self, n):
    '''
    Returns the TObject corresponding to entry n in the function's constant table.
    '''
    return self.proto.klist[n]

  def setk(self, n, val, tt=None):
    '''
    Set the given constant table entry. Equivalent to calling set() on the underlying TObject.
    '''
    self.proto.klist[n].set(val, tt=tt)

  def patch(self, i, code):
    '''
    Patch function bytecode starting at instruction i. Note that this is not
    atomic, each instruction is written individually.
    '''
    assert i+len(code) < self.proto.sizecode
    for opcode in code:
      # print(f'[patch {self.name}] @ {self.proto.codeptr:08X}[{i}]: {opcode.pprint(self.proto, i)}')
      self.proto.code[i](opcode)
      i += 1

  def dump(self, seen, indent=''):
    if self.isC:
      return
    if self.addr in seen:
      return
    seen[self.addr] = self

    # print(f'{indent}PROTO${self.proto.addr:08X}')
    if self.fenv.val().addr != seen.get('_G', None):
      print(f'{indent}FENV: {self.fenv}')
      self.fenv.dump(seen, indent + '  ')
    for i in range(self.proto.sizek):
      print(f'{indent}CONST${self.proto.k + i*8:08X} {f'k{i}':3} {self.proto.klist[i]}')

    print(f'{indent} CODE${self.proto.codeptr:08X}')
    for i,op in enumerate(self.proto.code):
      op = op()
      print(f'{indent}  {i:03d} {op.op:08X} {op.pprint(self.proto, i)}')

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
    self.metatable = Lua_GCTable(pine, pine.peek32(addr+8))
    self.size = pine.peek32(addr+12)
    # self.data = pine.readmem(addr+16, self.size)

  def __str__(self):
    return 'userdata$%08X[size=%d,mt=%s]' % (self.addr, self.size, self.metatable)

  def hasMetatable(self, seen):
    return (
      self.metatable is not None
      and self.metatable.tt() != LUA_TNIL
      and self.metatable.addr != seen['_METATABLE'])

  def dump(self, seen, indent = ''):
    if self.hasMetatable(seen):
      self.metatable.dump(seen, indent + '  ')

class Lua_GCThread(Lua_GCObject):
  def __init__(self, pine, addr):
    super().__init__(pine, addr)
    print(f'Loading lua_State${addr:08X}')

    self.stackbase = pine.peek32(addr + 0x1C)
    self.stacksize = pine.peek32(addr + 0x20)
    self.stacktop = pine.peek32(addr + 0x08)
    self.stack = [
      TObject(pine, self.stackbase + i*8)
      for i in range((self.stacktop - self.stackbase)//8 + 1)
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

  def lazyLoad(self):
    for node in self._G.val().hash:
      if node.k is not None and node.k.tt() == LUA_TSTRING and node.v is not None and node.v.tt() == LUA_TFUNCTION:
        node.v.val().name = node.k

  def __str__(self):
    return 'thread$%08X' % self.addr

  def getglobal(self, key) -> Lua_TObject:
    '''
    Returns the TObject for a given global (or None). Eqv to just calling getfield
    on _G.
    '''
    return self._G.val().getfield(key)

  def initialSeen(self):
    return {
      '_METATABLE': self._METATABLE.val().addr,
      '_G': self._G.val().addr,
    }

  def dump(self, seen, indent=''):
    self.lazyLoad()
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


# Implementations of GCObject
LUA_GCTYPES = [
  None, None, None, None,
  Lua_GCString, Lua_GCTable, Lua_GCFunction, Lua_GCUserdata, Lua_GCThread
]


def TObject(pine, addr):
  # if addr in _CACHE:
  #   return _CACHE[addr]
  # tt = pine.peek32(addr)
  # if tt == 0xFFFFFFFF:
  #   # Removed by garbage collector
  #   return None
  # print('creating tobject', f'{addr:08X} {tt} {pine.peek32(addr+4):08X}')
  return Lua_TObject(pine, addr)

def GCObject(pine, addr):
  if addr in _CACHE:
    return _CACHE[addr]
  tt = pine.peek8(addr+4)
  # print('creating gcobject', f'{addr:08X} {tt:X}')
  if tt == 0xFFFFFFFF:
    # Removed by garbage collector
    return None
  assert tt < len(LUA_GCTYPES), f'Unknown type {tt} constructing GCObject${addr:08X}'
  if LUA_GCTYPES[tt] is None:
    # wtf??
    return None
  assert LUA_GCTYPES[tt] is not None, f'Attempting to create gcobject${addr:08X} from primitive type {tt}'
  return LUA_GCTYPES[tt](pine, addr)
