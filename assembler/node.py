from collections import namedtuple
from enum import Enum, auto


class InstructionType(Enum):
    SIC = auto()
    ASSEMBLER = auto()


Instruction = namedtuple("Instruction", ["type", "label", "op", "operand"])
