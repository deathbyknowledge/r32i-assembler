#!/usr/bin/env python3
from typing import List


# lables define code blocks
def build_blocks_by_label(f):
  blocks = {}
  i = 0
  current_label = ""
  for line in f:
    cmt = line.find("#") # Find if there's a comment in the line
    if cmt != 0: 
      line = line[0:cmt]
      arr = [word for word in line.split(" ") if word != ""]
      if len(arr) == 0:
        continue
      print(i, arr)
    i = i+1



## Ops
from enum import Enum

regs = {
  'zero': 0, 'x0': 0,
  'ra': 1, 'x1': 1,
  'sp': 2, 'x2': 2,
  'gp': 3, 'x3': 3,
  'tp': 4, 'x4': 4,
  't0': 5, 'x5': 5,
  't1': 6, 'x6': 6,
  't2': 7, 'x7': 7,
  's0': 8, 'fp': 8, 'x8': 8,
  's1': 9, 'x9': 9,
  'a0': 10, 'x10': 10,
  'a1': 11, 'x11': 11,
  'a2': 12, 'x12': 12,
  'a3': 13, 'x13': 13,
  'a4': 14, 'x14': 14,
  'a5': 15, 'x15': 15,
  'a6': 16, 'x16': 16,
  'a7': 17, 'x17': 17,
  's2': 18, 'x18': 18,
  's3': 19, 'x19': 19,
  's4': 20, 'x20': 20,
  's5': 21, 'x21': 21,
  's6': 22, 'x22': 22,
  's7': 23, 'x23': 23,
  's8': 24, 'x24': 24,
  's9': 25, 'x25': 25,
  's10': 26, 'x26': 26,
  's11': 27, 'x27': 27,
  't3': 28, 'x28': 28,
  't4': 29, 'x29': 29,
  't5': 30, 'x30': 30,
  't6': 31, 'x31': 31,
}

OpFormat = Enum('OpFormat', ['R', 'I', 'S', 'U', 'J', 'B'])

class Literal():
  def __init__(self, name: str, value):
    self.name = name
    self.value = value
  
  def encode(self):
    return self.value

class Op():
  def __init__(self, name: str, opformat: OpFormat, opcode: int, func3=None, func7=None):
    self.name = name
    self.opformat = opformat
    self.opcode = opcode
    self.func3 = func3
    self.func7 = func7

  def encode(self, values: List[str]):
    # U-type
    if self.opformat == OpFormat.U: 
      assert(len(values) == 2) 

      rd = regs[values[0]]
      imm = int(values[1])
      return (imm << 12) + (rd << 7) + (self.opcode << 2) + 0b11

    # S-type
    elif self.opformat == OpFormat.S:
      assert(len(values) == 3)
      assert(self.func3 != None)

      rs2 = regs[values[0]]
      rs1 = regs[values[1]]
      imm = int(values[2])
      imm4_0 = (imm & 0b11111)
      imm11_5 = (imm & 0b111111100000) >> 5
      return (imm11_5 << 25) + (rs2 << 20) + (rs1 << 15) + (self.func3 << 12 ) + (imm4_0 << 7) + (self.opcode << 2) + 0b11

    # B-type
    elif self.opformat == OpFormat.B:
      assert(len(values) == 3)
      assert(self.func3 != None)

      rs1 = regs[values[0]]
      rs2 = regs[values[1]]
      imm = int(values[2])
      imm12 = (imm & 0x1000) >> 12
      imm11 = (imm & 0x800) >> 11
      imm10_5 = (imm & 0x7E0) >> 5
      imm4_1 = (imm & 0x1E) >> 1
      return  (imm12 << 30) + (imm10_5 << 25) + (rs2 << 20) + (rs1 << 15) + (self.func3 << 12 ) + (imm4_1 << 8) + (imm11 << 7) + (self.opcode << 2) + 0b11

    # I-type
    elif self.opformat == OpFormat.I:
      if self.name == 'fence':
        assert(len(values) == 2)
        pred = values[0]
        succ = values[1]
        pval = ((1 if 'i' in pred else 0) << 3) + ((1 if 'o' in pred else 0) << 2) + ((1 if 'r' in pred else 0) << 1) + (1 if 'w' in pred else 0)
        sval = ((1 if 'i' in succ else 0) << 3) + ((1 if 'o' in succ else 0) << 2) + ((1 if 'r' in succ else 0) << 1) + (1 if 'w' in succ else 0)
        return (pval << 24) + (sval << 20 ) + (self.opcode << 2 ) + 0b11

      else:
        assert(len(values) == 3)
        assert(self.func3 != None)

        rd = regs[values[0]]
        rs1 = regs[values[1]]
        imm = int(values[2])
        return (imm << 20) + (rs1 << 15) + (self.func3 << 12) + (rd << 7) + (self.opcode << 2) + 0b11

    # J-type
    elif self.opformat == OpFormat.J:
      assert(len(values) == 2)

      rd = regs[values[0]]
      imm = int(values[1])
      imm20 = (1 if imm < 0 else 0)
      imm10_1 = (imm & 2046) >> 1
      imm11 = (imm & 0x400) >> 10
      imm19_12 = (imm & 0x7F800) >> 11
      imm = (imm20 << 19) + (imm10_1 << 9) + (imm11 << 8) + imm19_12
      return (imm << 12) + (rd << 7) + (self.opcode << 2) + 0b11
    
    # R-type
    elif self.opformat == OpFormat.R:
      assert(len(values) == 3)
      assert(self.func3 != None)
      assert(self.func7 != None)

      rd = regs[values[0]]
      rs1 = regs[values[1]]
      rs2 = regs[values[2]]
      return (self.func7 << 25) + (rs2 << 20) + (rs1 << 15) + (self.func3 << 12 ) + (rd << 7) + (self.opcode << 2) + 0b11
    else:
      return Exception("unimplemented")



OPS = {
  'lui': Op('lui', OpFormat.U, 0b01101),
  'auipc': Op('auipc', OpFormat.U, 0b00101),
  'addi': Op('addi', OpFormat.I, 0b00100, func3=0b000),
  'slti': Op('slti', OpFormat.I, 0b00100, func3=0b010),
  'sltiu': Op('sltiu', OpFormat.I, 0b00100, func3=0b011),
  'xori': Op('xori', OpFormat.I, 0b00100, func3=0b011),
  'ori': Op('ori', OpFormat.I, 0b00100, func3=0b110),
  'andi': Op('andi', OpFormat.I, 0b00100, func3=0b111),
  'slli': Op('slli', OpFormat.I, 0b00100, func3=0b111),
  'srli': Op('srli', OpFormat.I, 0b00100, func3=0b101),
  'srai': Op('srai', OpFormat.I, 0b00100, func3=0b101),
  'add': Op('add', OpFormat.R, 0b1100, func3=0b000, func7=0b0000000),
  'sub': Op('sub', OpFormat.R, 0b1100, func3=0b000, func7=0b0100000),
  'sll': Op('sll', OpFormat.R, 0b1100, func3=0b001, func7=0b0000000),
  'slt': Op('slt', OpFormat.R, 0b1100, func3=0b010, func7=0b0000000),
  'sltu': Op('sltu', OpFormat.R, 0b1100, func3=0b011, func7=0b0000000),
  'xor': Op('xor', OpFormat.R, 0b1100, func3=0b100, func7=0b0000000),
  'srl': Op('srl', OpFormat.R, 0b1100, func3=0b101, func7=0b0000000),
  'sra': Op('sra', OpFormat.R, 0b1100, func3=0b101, func7=0b0100000),
  'or': Op('or', OpFormat.R, 0b1100, func3=0b110, func7=0b0000000),
  'and': Op('and', OpFormat.R, 0b1100, func3=0b111, func7=0b0000000),
  'fence': Op('fence', OpFormat.I, 0b0011, func3=0b000),
  'ecall': Literal('ecall', 0b1110011),
  'ebreak': Literal('ebreak', 1048691),
  'lb': Op('lb', OpFormat.I, 0b00000, func3=0b000),
  'lh': Op('lh', OpFormat.I, 0b00000, func3=0b001),
  'lw': Op('lw', OpFormat.I, 0b00000, func3=0b010),
  'lbu': Op('lbu', OpFormat.I, 0b00000, func3=0b100),
  'lhu': Op('lhu', OpFormat.I, 0b00000, func3=0b101),
  'sb': Op('sb', OpFormat.S, 0b01000, func3=0b000),
  'sh': Op('sh', OpFormat.S, 0b01000, func3=0b001),
  'sw': Op('sw', OpFormat.S, 0b01000, func3=0b010),
  'jal': Op('jal', OpFormat.J, 0b11011),
  'jalr': Op('jalr', OpFormat.I, 0b11001, func3=0b000),
  'beq': Op('beq', OpFormat.B, 0b11000, func3=0b000),
  'bne': Op('bne', OpFormat.B, 0b11000, func3=0b001),
  'blt': Op('blt', OpFormat.B, 0b11000, func3=0b100),
  'bge': Op('bge', OpFormat.B, 0b11000, func3=0b101),
  'bltu': Op('bltu', OpFormat.B, 0b11000, func3=0b110),
  'bgeu': Op('bgeu', OpFormat.B, 0b11000, func3=0b111),
}



def test():
  # lui x1, 101
  assert(OPS['lui'].encode(['x1', '101']) == 0x000650b7)
  # addi x1, x0, 3
  assert(OPS['addi'].encode(['x1', 'x0', '3']) == 0x00300093)
  # addi ra, s2, 1002
  assert(OPS['addi'].encode(['ra', 's2', '1002']) == 0x3ea90093)
  # add x12, x3, x2
  assert(OPS['add'].encode(['x12', 'x3', 'x2']) == 0x00218633)
  # add a2, gp, sp
  assert(OPS['add'].encode(['a2', 'gp', 'sp']) == 0x00218633)
  # sll ra, s2, s3
  assert(OPS['sll'].encode(['ra', 's2', 's3']) == 0x013910b3)
  # srl ra, s2, s3
  assert(OPS['srl'].encode(['ra', 's2', 's3']) == 0x013950b3)
  # sra ra, s2, s3
  assert(OPS['sra'].encode(['ra', 's2', 's3']) == 0x413950b3)
  # jal ra, -8
  assert(OPS['jal'].encode(['ra', '-8']) == 0xff9ff0ef)
  # jal ra, 128
  assert(OPS['jal'].encode(['ra', '128']) == 0x080000ef)
  # jalr t3, 8(ra)
  assert(OPS['jalr'].encode(['t3', 'ra', '8']) == 0x00808e67)
  # ori x8, x9, 255
  assert(OPS['ori'].encode(['x8', 'x9', '255']) == 0x0ff4e413)
  # beq s2, t0, 8
  assert(OPS['beq'].encode(['s2', 't0', '8']) == 0x00590463)
  # bne s3, t6, 0
  assert(OPS['bne'].encode(['s3', 't6', '0']) == 0x01f99063)
  # blt x19, x31, 0
  assert(OPS['blt'].encode(['x19', 'x31', '0']) == 0x01f9c063)
  # bgeu x19, x31, 32
  assert(OPS['bgeu'].encode(['x19', 'x31', '32']) == 0x03f9f063)
  # sw sp, 16(x3)
  assert(OPS['sw'].encode(['sp', 'gp', '16']) == 0x0021a823)
  # sb x10, 0(x11)
  assert(OPS['sb'].encode(['x10', 'x11', '0']) == 0x00a58023)
  # lb x10, 0(x11)
  assert(OPS['lb'].encode(['x10', 'x11', '0']) == 0x00058503)
  # fence iorw, iorw
  assert(OPS['fence'].encode(['iorw', 'iorw']) == 0x0ff0000f)

if __name__ == "__main__":
  import sys
  if len(sys.argv) > 1:
    with open(sys.argv[1], 'r') as f:
      test()
      build_blocks_by_label(f)
  else:
    print(f"Missing file. Usage: {sys.argv[0]} [filepath]")

