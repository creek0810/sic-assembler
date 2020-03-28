from node import Instruction, InstructionType

from sic import OPERATION


class SicParser:
    """this class will parse input file to a list of instructions"""

    def __init__(self, file_name):
        self.file_name = file_name
        self.asm_inst = [
            "START",
            "END",
            "BYTE",
            "WORD",
            "RESB",
            "RESW",
            "BASE",
            "NOBASE",
        ]

    def _clean_token(self, token_list):
        for idx, token in enumerate(token_list):
            if token[0] in ("+", "@", "#"):
                token_list[idx] = token[1:]

    def _parse_instruction(self, line):
        token_list = line.replace(",", " ").split()
        if len(token_list) < 1:
            return None
        # token_list[0] may be
        # 1. asm instruction
        # 2. sic instruction
        # 3. label
        if token_list[0] in OPERATION or (
            token_list[0][0] == "+" and token_list[0][1:] in OPERATION
        ):
            e = int(token_list[0][0] == "+")
            # check if the instruction is immediate or indirect
            n = 0
            i = 0
            if len(token_list) >= 2:
                i = int(token_list[1][0] == "#")
                n = int(token_list[1][0] == "@")

            self._clean_token(token_list)

            if len(token_list) > 1:
                cur_operand = token_list[1:]
            else:
                cur_operand = None

            return Instruction(
                type=InstructionType.SIC,
                label=None,
                op=token_list[0],
                operand=cur_operand,
                e=e,
                n=n,
                i=i,
            )
        elif token_list[0] in self.asm_inst:

            self._clean_token(token_list)
            return Instruction(
                type=InstructionType.ASSEMBLER,
                label=None,
                op=token_list[0],
                operand=token_list[1:],
                n=0,
                i=0,
                e=0,
            )
        else:
            # immediate flag and indirect flag
            n = 0
            i = 0
            if token_list[1] in OPERATION or (
                token_list[1][0] == "+" and token_list[1][1:] in OPERATION
            ):
                cur_type = InstructionType.SIC
                e = int(token_list[1][0] == "+")

                # check if immediate or indirect
                if len(token_list) >= 3:
                    i = int(token_list[2][0] == "#")
                    n = int(token_list[2][0] == "@")
            else:
                cur_type = InstructionType.ASSEMBLER
                e = 0

            self._clean_token(token_list)

            return Instruction(
                type=cur_type,
                label=token_list[0],
                op=token_list[1],
                operand=token_list[2:],
                e=e,
                i=i,
                n=n,
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
