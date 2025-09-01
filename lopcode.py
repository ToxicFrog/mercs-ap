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

class LuaOpcode:
  def __init__(self, op):
    self.op  = op
    self.I   = (op & 0x0000003F) >>  0
    self.A   = (op & 0xFF000000) >> 24
    self.B   = (op & 0x00FF8000) >> 15
    self.C   = (op & 0x00007FC0) >>  6
    self.Bx  = (op & 0x00FFFFC0) >>  6
    self.sBx = self.Bx - 131071

  def Kst(self, proto, idx):
    return f'{proto.klist[idx]}'

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
      case  4: return f' GETUPVAL r{A} := UV[{B}]'
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
      case 21:
        if A == 0:
          return f'      BEQ {self.RK(proto, B)} == {self.RK(proto, C)}'
        else:
          return f'      BNE {self.RK(proto, B)} != {self.RK(proto, C)}'
      case 22:
        if A == 0:
          return f'      BLT {self.RK(proto, B)} < {self.RK(proto, C)}'
        else:
          return f'      BGE {self.RK(proto, B)} >= {self.RK(proto, C)}'
      case 23:
        if A == 0:
          return f'      BLE {self.RK(proto, B)} <= {self.RK(proto, C)}'
        else:
          return f'      BGT {self.RK(proto, B)} > {self.RK(proto, C)}'
      # OP_TEST,/*      A B C   if (R(B) <=> C) then R(A) := R(B) else pc++     */
      # ????
      case 24:
        if C == 0:
          return f'     TEST not r{A}: r{A} := r{B} ; or skip'
        else:
          return f'     TEST r{A}: r{A} := r{B} ; or skip'
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

"""
** R(x) - register
** Kst(x) - constant (in constant table)
** RK(x) == if x < MAXSTACK then R(x) else Kst(x-MAXSTACK)

typedef enum {
/*----------------------------------------------------------------------
name            args    description
------------------------------------------------------------------------*/

OP_CALL,/*      A B C   R(A), ... ,R(A+C-2) := R(A)(R(A+1), ... ,R(A+B-1)) */
OP_TAILCALL,/*  A B C   return R(A)(R(A+1), ... ,R(A+B-1))              */
OP_RETURN,/*    A B     return R(A), ... ,R(A+B-2)      (see note)      */

OP_FORLOOP,/*   A sBx   R(A)+=R(A+2); if R(A) <?= R(A+1) then PC+= sBx  */

OP_TFORLOOP,/*  A C     R(A+2), ... ,R(A+2+C) := R(A)(R(A+1), R(A+2));
                        if R(A+2) ~= nil then pc++                      */
OP_TFORPREP,/*  A sBx   if type(R(A)) == table then R(A+1):=R(A), R(A):=next;
                        PC += sBx                                       */

OP_SETLIST,/*   A Bx    R(A)[Bx-Bx%FPF+i] := R(A+i), 1 <= i <= Bx%FPF+1 */
OP_SETLISTO,/*  A Bx                                                    */

OP_CLOSE,/*     A       close all variables in the stack up to (>=) R(A)*/
OP_CLOSURE/*    A Bx    R(A) := closure(KPROTO[Bx], R(A), ... ,R(A+n))  */
} OpCode;
"""
