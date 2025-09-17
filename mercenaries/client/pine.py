import socket
import struct
from typing import NamedTuple


_INT_FORMATS = { 8: '< B', 16: '< H', 32: '< I', 64: '< Q'}


class PineStatus(NamedTuple):
  title: str
  id: str
  uuid: str
  version: str


class Pine:
  sock: socket.socket

  def __init__(self, path: str = None, address: str = None):
    assert path or address, "Pine requires a path or address"

    if path:
      self.sock = socket.socket(family = socket.AF_UNIX, type = socket.SOCK_STREAM)
      self.sock.connect(path)

    elif address:
      address = tuple(address.split(':'))
      self.sock = socket.create_connection(address)

    else:
      raise NotImplementedError

  def send(self, opcode: int, payload: bytes = b''):
    size = len(payload) + 5
    data = struct.pack('< I B %ds' % len(payload), size, opcode, payload)
    # print('>>', size, opcode, data)
    return self.sock.send(data)

  def recv(self):
    header = self.sock.recv(5)
    (size, result) = struct.unpack('< I B', header)
    if result > 0:
      # print('<<', header, size, result)
      return None
    if size > 5:
      data = self.sock.recv(size-5)
      # print('<<', header, size, result, data)
      return data
    else:
      # print('<<', header, size, result, b'')
      return b''

  def command(self, opcode: int, unpack, payload: bytes = b''):
    self.send(opcode, payload)
    data = self.recv()
    assert data is not None, f"Error receiving reply for command {opcode}"
    return unpack(data)

  def pack(self, bits: int, n: int, *args):
    buf = struct.pack(_INT_FORMATS[bits], n)
    if len(args) == 0:
      return buf
    else:
      return buf + self.pack(*args)

  def unpack_empty(self, data: bytes):
    assert data == b'', f'Non-empty response: {data}'
    return None

  def unpack_string(self, data: bytes):
    size = struct.unpack('< I', data[0:4])[0]
    assert len(data) == size+4, 'String consistency error, size=%d len(data)=%d' % (size, len(data))
    return data[4:-1].decode(errors='replace')

  def unpack_float(self, data: bytes):
    return struct.unpack('< f', data)[0]

  def int_unpacker(self, bits: int):
    def unpack_int(data: bytes):
      return struct.unpack(_INT_FORMATS[bits], data)[0]
    return unpack_int

  # Higher-level commands to make it easier to wiggle the game.

  def game_info(self):
    return PineStatus(
      self.command(0x0B, self.unpack_string),
      self.command(0x0C, self.unpack_string),
      self.command(0x0D, self.unpack_string),
      self.command(0x0E, self.unpack_string))

  def peek8(self, addr):
    return self.command(0x00, self.int_unpacker(8), self.pack(32, addr))
  def peek16(self, addr):
    return self.command(0x01, self.int_unpacker(16), self.pack(32, addr))
  def peek32(self, addr):
    return self.command(0x02, self.int_unpacker(32), self.pack(32, addr))
  def peek64(self, addr):
    return self.command(0x03, self.int_unpacker(64), self.pack(32, addr))

  def peekf32(self, addr):
    return self.command(0x02, self.unpack_float, self.pack(32, addr))

  def poke8(self, addr, n):
    return self.command(0x04, self.unpack_empty, self.pack(32, addr, 8, n))
  def poke16(self, addr, n):
    return self.command(0x05, self.unpack_empty, self.pack(32, addr, 16, n))
  def poke32(self, addr, n):
    return self.command(0x06, self.unpack_empty, self.pack(32, addr, 32, n))
  def poke64(self, addr, n):
    return self.command(0x07, self.unpack_empty, self.pack(32, addr, 64, n))

  def pokef32(self, addr, n):
    return self.command(0x06, self.unpack_empty, self.pack(32, addr) + struct.pack('< f', n))

  def readmem(self, addr, size):
    buf = b''
    while size >= 8:
      buf = buf + self.command(0x03, lambda x: x, self.pack(32, addr))
      addr += 8
      size -= 8
    while size > 0:
      buf = buf + self.command(0x00, lambda x: x, self.pack(32, addr))
      addr += 1
      size -= 1
    return buf

  def writemem(self, addr, data):
    while len(data) >= 8:
      self.command(0x07, self.unpack_empty, self.pack(32, addr) + data[:8])
      addr += 8
      data = data[8:]
    while len(data) > 0:
      self.command(0x04, self.unpack_empty, self.pack(32, addr) + data[:1])
      addr += 1
      data = data[1:]

  def readstring(self, addr, size):
    return self.readmem(addr, size).decode(errors='replace')

