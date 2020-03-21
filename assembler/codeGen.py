import sys

from node import InstructionType

from sic import OPERATION


class CodeGen:
    def __init__(self):
        self.symbol = {}
        self.starting = 0
        self.locctr = 0
        self.reg = {
            "A": 0,
            "X": 1,
            "L": 2,
            "PC": 8,
            "SW": 9,
            "B": 3,
            "S": 4,
            "T": 5,
            "F": 6,
        }

    def _pass1(self, tree):
        """ this function will build symbol table and calc locctr"""
        cur_idx = 0
        if tree[cur_idx].op == "START":
            self.starting = self.locctr = int(tree[cur_idx].operand[0], 16)
            cur_idx += 1

        while cur_idx < len(tree):
            cur_node = tree[cur_idx]
            cur_idx += 1

            if cur_node.op == "END":
                break
            # establish symbol table
            if cur_node.label:
                # deal with duplicate label problem
                if cur_node.label in self.symbol:
                    print(f"Duplicate label: {cur_node.label}")
                    sys.exit(1)
                self.symbol[cur_node.label] = self.locctr
            # update locctr
            if cur_node.type == InstructionType.SIC:
                self.locctr += 3
            elif cur_node.op == "WORD":
                self.locctr += 3
            elif cur_node.op == "RESB":
                self.locctr += int(cur_node.operand[0])
            elif cur_node.op == "RESW":
                self.locctr += int(cur_node.operand[0]) * 3
            elif cur_node.op == "BYTE":
                if cur_node.operand[0][0] == "X":
                    self.locctr += int((len(cur_node.operand[0]) - 3) / 2)
                elif cur_node.operand[0][0] == "C":
                    self.locctr += len(cur_node.operand[0]) - 3
            else:
                print("Invalid instruction: {cur_node.op}")
                sys.exit(1)

    def _write_header(self, program_name=None):
        # 1. START 1000
        # 2. ADDEX START 1000
        if program_name and len(program_name) > 6:
            print("Program name should less than 7 letters")
            sys.exit(1)
        program_name = program_name.ljust(6)
        starting = "{:06X}".format(self.starting)
        program_len = "{:06X}".format(self.locctr - self.starting)
        print(f"H{program_name}{starting}{program_len}")

    def _write_code(self, starting, code):
        if len(code):
            starting = "{:06X}".format(starting)
            record_len = "{:02X}".format(len(code) // 2)
            print(f"T{starting}{record_len}{code}")

    def _write_end(self, first=None):
        if first:
            first = "{:06X}".format(first)
        else:
            first = "{:06X}".format(self.starting)
        print(f"E{first}")

    def _char_2_byte(self, char):
        result = ""
        for ch in char:
            # char -> ascii -> hex
            result += "{:02X}".format(ord(ch))
        return result

    def _gen_f2(self, instruction):
        opcode = OPERATION[instruction.op]["code"]

        if instruction.op == "SVC":
            r1 = self.reg[instruction.operand[0]]
            r2 = "0"
        elif instruction.op == "CLEAR" or instruction.op == "TIXR":
            r1 = self.reg[instruction.operand[0]]
            r2 = "0"
        elif instruction.op == "SHIFTL" or instruction.op == "SHIFTR":
            r1 = self.reg[instruction.operand[0]]
            r2 = int(instruction.operand[1]) - 1
        else:
            # general case
            r1 = self.reg[instruction.operand[0]]
            r2 = self.reg[instruction.operand[1]]
        return f"{opcode}{r1}{r2}"

    def _gen_instruction(self, instruction):
        # todo: support index
        if OPERATION[instruction.op]["format"] == "1":
            pass
        elif OPERATION[instruction.op]["format"] == "2":
            return self._gen_f2(instruction)

        if instruction.operand is None:
            return OPERATION[instruction.op]["code"] + "0000"
        elif instruction.operand[0] in self.symbol:
            tmp_loc = self.symbol[instruction.operand[0]]
            tmp_loc = "{:04X}".format(tmp_loc)
            return OPERATION[instruction.op]["code"] + tmp_loc
        else:
            print(f"Undefined symbol: {cur_node.operand[0]}")
            sys.exit(1)

    def _pass2(self, tree):
        cur_idx = 0
        # build header
        if tree[cur_idx].op == "START":
            self._write_header(tree[cur_idx].label)
            cur_idx += 1
        else:
            self._write_header()
        # build text
        code_buffer = ""
        cur_addr = self.starting
        while cur_idx < len(tree):
            cur_node = tree[cur_idx]
            if cur_node.op == "END":
                break
            cur_idx += 1

            # gen code
            if cur_node.type == InstructionType.SIC:
                cur_code = self._gen_instruction(cur_node)
            elif cur_node.op == "WORD":
                cur_code = "{:06X}".format(int(cur_node.operand[0]))
            elif cur_node.op == "RESB":
                # force flush
                byte_len = int(cur_node.operand[0]) * 2
                self._write_code(cur_addr, code_buffer)
                cur_addr += int((len(code_buffer) + byte_len) / 2)
                code_buffer = ""
                continue
            elif cur_node.op == "RESW":
                # force flush
                byte_len = int(cur_node.operand[0]) * 3 * 2
                self._write_code(cur_addr, code_buffer)
                cur_addr += int((len(code_buffer) + byte_len) / 2)
                code_buffer = ""
                continue
            elif cur_node.op == "BYTE":
                if cur_node.operand[0][0] == "X":
                    cur_code = cur_node.operand[0][2:-1]
                elif cur_node.operand[0][0] == "C":
                    # todo
                    cur_code = self._char_2_byte(cur_node.operand[0][2:-1])
            # check if need to flush code
            print(cur_node.op, cur_node.operand, cur_code)

            if len(code_buffer + cur_code) <= 60:
                code_buffer += cur_code
            else:
                self._write_code(cur_addr, code_buffer)
                cur_addr += int(len(code_buffer) / 2)
                code_buffer = cur_code
        # clear buffer
        self._write_code(cur_addr, code_buffer)
        cur_addr += int(len(code_buffer) / 2)

        # build end
        if tree[cur_idx].operand[0]:
            tmp_loc = self.symbol[tree[cur_idx].operand[0]]
            self._write_end(tmp_loc)
        else:
            self._write_end()

    def gen(self, tree):
        # build symbol table and calc locctr
        self._pass1(tree)
        # code gen
        self._pass2(tree)
