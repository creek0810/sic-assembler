from node import Instruction, InstructionType

from sic import OPERATION


class SicParser:
    """this class will parse input file to a list of instructions
        type: maybe 'sic', 'assembler'
        label: label
        op: op
        operand: a list contains operand
    """

    def __init__(self, file_name):
        self.file_name = file_name
        self.asm_inst = ["START", "END", "BYTE", "WORD", "RESB", "RESW"]

    def _parse_instruction(self, line):
        token_list = line.replace(",", " ").split()
        if len(token_list) < 1:
            return None
        # token_list[0] can be a
        # 1. asm instruction
        # 2. sic instruction
        # 3. label
        if token_list[0] in OPERATION:
            if len(token_list) > 1:
                cur_operand = token_list[1:]
            else:
                cur_operand = None

            return Instruction(
                type=InstructionType.SIC,
                label=None,
                op=token_list[0],
                operand=cur_operand,
            )
        elif token_list[0] in self.asm_inst:
            return Instruction(
                type=InstructionType.ASSEMBLER,
                label=None,
                op=token_list[0],
                operand=token_list[1:],
            )
        else:
            if token_list[1] in OPERATION:
                cur_type = InstructionType.SIC
            else:
                cur_type = InstructionType.ASSEMBLER
            return Instruction(
                type=cur_type,
                label=token_list[0],
                op=token_list[1],
                operand=token_list[2:],
            )

    def parse(self):
        result = []
        with open(self.file_name, "r+") as file:
            for line in file.readlines():
                # ignore comment line
                if line.startswith("."):
                    continue
                # parse
                cur_node = self._parse_instruction(line)
                if cur_node:
                    result.append(cur_node)
        return result
