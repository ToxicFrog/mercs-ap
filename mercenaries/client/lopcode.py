"""
Lua opcodes are 32 bits and have the following formats, lsb last:

  AAAAAAAA BBBBBBBB BCCCCCCC CCIIIIII - 'A B C' format
  AAAAAAAA BBBBBBBB BBBBBBBB BBIIIIII - 'A Bx' format
  AAAAAAAA BBBBBBBB BBBBBBBB BBIIIIII - 'A sBx' format; B is signed

- A holds [0..255]
- B and C hold [0..511]
- Bx holds [0..262143]

Signed fields are stored as offsets rather than sign-magnitude or 2s-complement.
That is to say, sBx = Bx - K, where K is (max value of Bx >> 1), or 131071

"""

OPNAMES = [
  "MOVE",
  "LOADK",
  "LOADBOOL",
  "LOADNIL",
  "GETUPVAL",
  "GETGLOBAL",
  "GETTABLE",
  "SETGLOBAL",
  "SETUPVAL",
  "SETTABLE",
  "NEWTABLE",
  "SELF",
  "ADD",
  "SUB",
  "MUL",
  "DIV",
  "POW",
  "UNM",
  "NOT",
  "CONCAT",
  "JMP",
  "EQ",
  "LT",
  "LE",
  "TEST",
  "CALL",
  "TAILCALL",
  "RETURN",
  "FORLOOP",
  "TFORLOOP",
  "TFORPREP",
  "SETLIST",
  "SETLISTO",
  "CLOSE",
  "CLOSURE"
]
OP = {
  name: index
  for (index,name) in enumerate(OPNAMES)
}

class LuaOpcode:
  def __init__(self, op, **kwargs):
    if len(kwargs) > 0:
      self.initByParts(I=op, **kwargs)
      return
    self.op  = op
    self.I   = (op & 0x0000003F) >>  0
    self.A   = (op & 0xFF000000) >> 24
    self.B   = (op & 0x00FF8000) >> 15
    self.C   = (op & 0x00007FC0) >>  6
    self.Bx  = (op & 0x00FFFFC0) >>  6
    self.sBx = self.Bx - 131071

  def __repr__(self):
    return f'LuaOpcode({self.op:08x}, {OPNAMES[self.I] if self.I in OPNAMES else self.I}, A={self.A}, B={self.B}, C={self.B}, Bx={self.Bx}, sBx={self.sBx})'

  def initByParts(self, I, A=None, B=None, C=None, Bx=None, sBx=None):
    self.I = OP[I] if I in OP else I
    self.A = A or 0
    if Bx is not None:
      assert B is None and C is None and sBx is None
      self.Bx = Bx
      self.sBx = Bx - 131071
      self.B = (self.Bx >> 9) * 0x1FF
      self.C = self.Bx & 0x1FF
    elif sBx is not None:
      assert B is None and C is None and Bx is None
      self.Bx = sBx + 131071
      self.sBx = sBx
      self.B = (self.Bx >> 9) * 0x1FF
      self.C = self.Bx & 0x1FF
    else:
      self.B = B or 0
      self.C = C or 0
      self.Bx = (self.B << 9) + self.C
      self.sBx = self.Bx - 131071

    self.op = (self.A << 24) | (self.B << 15) | (self.C << 6) | self.I

    tmp = LuaOpcode(self.op)
    assert tmp.I == self.I and tmp.A == self.A and tmp.Bx == self.Bx, f'{self} != {tmp}'


  def Kst(self, proto, idx):
    return f'k{idx} ({proto.klist[idx]})'

  def RK(self, proto, idx):
    if idx < 250: # MAXSTACK
      return f'r{idx}'
    else:
      return self.Kst(proto, idx - 250)

  def pprint(self, proto, addr):
    (A, B, C, Bx, sBx) = (self.A, self.B, self.C, self.Bx, self.sBx)
    match self.I:
      case  0: return f'     MOVE r{A} := r{B}'
      case  1: return f'    LOADK r{A} := {self.Kst(proto, Bx)}'
      case  2: return f' LOADBOOL r{A} := {B != 0}{C != 0 and f' ; br {addr+2}' or ''}'
      case  3: return f'  LOADNIL r{A} ... r{B}'
      case  4: return f' GETUPVAL r{A} := u{B}'
      case  5: return f'GETGLOBAL r{A} := _G[{self.Kst(proto, Bx)}]'
      case  6: return f' GETTABLE r{A} := r{B}[{self.RK(proto, C)}]'
      case  7: return f'SETGLOBAL r{A} ->> _G[{self.Kst(proto, Bx)}]'
      case  8: return f' SETUPVAL r{A} ->> UV[{B}]'
      case  9: return f' SETTABLE {self.RK(proto, C)} ->> r{A}[{self.RK(proto, B)}]'
      case 10: return f' NEWTABLE r{A} := {'{}'} (#a={B}, #h={C})'
      case 11: return f'     SELF r{A+1} := r{B} ; r{A} := r{B}[{self.RK(proto, C)}]'
      case 12: return f'      ADD r{A} := {self.RK(proto, B)} + {self.RK(proto, C)}'
      case 13: return f'      SUB r{A} := {self.RK(proto, B)} - {self.RK(proto, C)}'
      case 14: return f'      MUL r{A} := {self.RK(proto, B)} * {self.RK(proto, C)}'
      case 15: return f'      DIV r{A} := {self.RK(proto, B)} / {self.RK(proto, C)}'
      case 16: return f'      POW r{A} := {self.RK(proto, B)} ^ {self.RK(proto, C)}'
      case 17: return f'      UNM r{A} := -r{B}'
      case 18: return f'      NOT r{A} := not r{B}'
      case 19: return f'   CONCAT r{A} := r{B} ... r{C}'
      case 20: return f'      JMP {sBx:+d} ; {addr+sBx+1}'
      case 21: return f'       EQ {self.RK(proto, B)} {'==' if A else '!='} {self.RK(proto, C)}'
      case 22: return f'       LT {self.RK(proto, B)} {'<' if A else '>='} {self.RK(proto, C)}'
      case 23: return f'       LE {self.RK(proto, B)} {'<=' if A else '>'} {self.RK(proto, C)}'
      case 24: return f'     TEST {'' if C else 'not '}r{B} : r{A} := r{B}'
      case 25: return f'     CALL r{A} ({B-1} args) => {C-1} results'
      case 26: return f' TAILCALL r{A} ({B-1} args)'
      case 27: return f'   RETURN r{A} ... r{A+B-2}'
      case 28: return f'  FORLOOP r{A} := r{A+2}; if r{A} <= r{A+1} JMP {sBx:+d}'
      case 29: return f' TFORLOOP WIP'
      case 30: return f' TFORPREP WIP'
      case 31: return f'  SETLIST r{A} [{Bx}]'
      case 32: return f' SETLISTO r{A} [{Bx}]'
      case 33: return f'    CLOSE r{A} ...'
      case 34: return f'  CLOSURE r{A} := closure({Bx}, r{A}...)'

      case  _: return f'<<invalid opcode: {self.op:08X}>>'
