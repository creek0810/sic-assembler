from collections import namedtuple
from enum import Enum, auto


class InstructionType(Enum):
    SIC = auto()
    ASSEMBLER = auto()


"""
    type: instruction type. May be "SIC", "ASSEMBLER"
    label: label
    op: operation
    e: extend
    i: immediate
    n: indirect
"""
Instruction = namedtuple(
    "Instruction", ["type", "label", "op", "operand", "e", "n", "i"]
)
