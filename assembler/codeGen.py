import sys

from node import InstructionType

from sic import OPERATION


class CodeGen:
    def __init__(self):
        # preload reg into symbol table
        self.symbol = {
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
        self.starting = 0
        self.ending = 0

    # write function
    def _write_header(self, program_name=None):
        # 1. START 1000
        # 2. ADDEX START 1000
        if program_name and len(program_name) > 6:
            print("Program name should less than 7 letters")
            sys.exit(1)
        program_name = program_name.ljust(6)
        starting = "{:06X}".format(self.starting)
        program_len = "{:06X}".format(self.ending - self.starting)
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

    # help function
    def _char_2_byte(self, char):
        result = ""
        for ch in char:
            # char -> ascii -> hex
            result += "{:02X}".format(ord(ch))
        return result

    # codegen function
    def _instruction_size(self, instruction):
        if instruction.type == InstructionType.SIC:
            # format x = x bytes
            if instruction.e:
                return 4
            else:
                return int(OPERATION[instruction.op]["format"])
        elif instruction.op == "WORD":
            return 3
        elif instruction.op == "RESB":
            return int(instruction.operand[0])
        elif instruction.op == "RESW":
            return int(instruction.operand[0]) * 3
        elif instruction.op == "BYTE":
            if instruction.operand[0][0] == "X":
                return int((len(instruction.operand[0]) - 3) / 2)
            elif instruction.operand[0][0] == "C":
                return len(instruction.operand[0]) - 3
        elif instruction.op == "BASE" or instrunction.op == "NOBASE":
            return 0
        else:
            print(f"Invalid instruction: {instruction.op}")
            exit(1)

    def _pass1(self, tree):
        """ this function will build symbol table and calc locctr """
        cur_idx = 0
        if tree[cur_idx].op == "START":
            self.starting = locctr = int(tree[cur_idx].operand[0], 16)
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
                self.symbol[cur_node.label] = locctr
            # update locctr
            locctr += self._instruction_size(cur_node)

        self.ending = locctr

    def _gen_f2(self, instruction):
        """
        format:
            ---------------
            | op | r1 | r2 |
            --------------
            |  8 |  4 |  4 |
            ---------------
        """
        # establish opcode
        opcode = "{:02X}".format(OPERATION[instruction.op]["code"])
        # establish r1, r2
        if instruction.op == "SVC":
            r1 = self.symbol[instruction.operand[0]]
            r2 = "0"
        elif instruction.op == "CLEAR" or instruction.op == "TIXR":
            r1 = self.symbol[instruction.operand[0]]
            r2 = "0"
        elif instruction.op == "SHIFTL" or instruction.op == "SHIFTR":
            r1 = self.symbol[instruction.operand[0]]
            # warning: don't forget to convert to hex
            r2 = "{:02X}".format(int(instruction.operand[1]) - 1)
        else:
            # general case
            r1 = self.symbol[instruction.operand[0]]
            r2 = self.symbol[instruction.operand[1]]
        return f"{opcode}{r1}{r2}"

    def _gen_f3_i_n_opcode(self, instruction):
        """ gen immediate and indirect code """
        """
        format:
            --------------
            | op | n | i |
            --------------
            |  6 | 1 | 1 |
            --------------
        """
        tmp_code = OPERATION[instruction.op]["code"]
        if instruction.n:
            tmp_code += 2
        elif instruction.i:
            tmp_code += 1
        return "{:02X}".format(tmp_code)

    def _gen_f3_addr(self, instruction, pc, base):
        """ trying seq
            1. pc relative mode (-2048 ~ 2047)
            2. base relative mode (0 ~ 4095)
        """
        # x b p e
        address_mode = 0
        # x
        if instruction.operand and len(instruction.operand) == 2:
            address_mode += 1 << 3
        # b or p or e
        if instruction.e:
            address_mode += 1
            disp = "{:05X}".format(self.symbol[instruction.operand[0]])
        elif -2048 <= self.symbol[instruction.operand[0]] - pc <= 2047:
            # pc relative
            address_mode += 1 << 1
            loc = self.symbol[instruction.operand[0]] - pc
            if loc < 0:
                disp = hex((1 << 12) + loc).upper()[2:]
            else:
                disp = "{:03X}".format(loc)
        elif base and 0 <= self.symbol[instruction.operand[0]] - base <= 4095:
            # base relative
            address_mode += 1 << 2
            disp = "{:03X}".format(self.symbol[instruction.operand[0]] - base)
        else:
            disp = "{:03X}".format(self.symbol[instruction.operand[0]])
            """
            print(pc, self.symbol[instruction.operand[0]])
            print("Please change the format to 4:", instruction)
            exit(1)
            """
        address_mode = "{:01X}".format(address_mode)
        return f"{address_mode}{disp}"

    def _gen_sic(self, instruction):
        # deal with special case "RSUB"
        if instruction.op == "RSUB":
            return "{:02X}0000".format(OPERATION[instruction.op]["code"])

        # gen op part
        opcode = "{:02X}".format(OPERATION[instruction.op]["code"])
        # gen x and address
        if instruction.operand[0] in self.symbol:
            address = self.symbol[instruction.operand[0]]
        else:
            print(f"Undefined symbol: {instruction.operand[0]}")
            exit(1)

        if len(instruction.operand) == 2 and instruction.operand[1] == "X":
            address += 1 << 15

        address = "{:04X}".format(address)
        return f"{opcode}{address}"

    def _gen_f34(self, instruction, pc, base):
        # deal with special case "RSUB"
        if instruction.op == "RSUB":
            return "{:02X}0000".format(OPERATION[instruction.op]["code"] + 3)

        result = ""
        # immediate or indirect instruction
        if instruction.i == 1 or instruction.n == 1:
            # gen op part
            result = self._gen_f3_i_n_opcode(instruction)
            # gen x, b, p, e and disp
            if instruction.e == 1:
                result += "1" + "{:05X}".format(int(instruction.operand[0]))
            else:
                # TODO: symbol immediate
                if instruction.operand[0] in self.symbol:
                    result += self._gen_f3_addr(instruction, pc, base)
                else:
                    result += "0" + "{:03X}".format(int(instruction.operand[0]))
            return result
        # sic instruction
        # elif OPERATION[instruction.op]["sic"]:
        #     return self._gen_sic(instruction)
        # sic xe simple instruction
        else:
            # gen op part
            tmp_code = OPERATION[instruction.op]["code"] + 3
            result = "{:02X}".format(tmp_code)
            # gen x, b, p, e and address
            result += self._gen_f3_addr(instruction, pc, base)
            return result

    def _gen_instruction(self, instruction, pc, base):
        if OPERATION[instruction.op]["format"] == "1":
            return "{:02X}".format(OPERATION[instruction.op]["code"])
        elif OPERATION[instruction.op]["format"] == "2":
            return self._gen_f2(instruction)
        else:
            return self._gen_f34(instruction, pc, base)

    def _pass2(self, tree):
        # TODO: support base relative
        cur_idx = 0
        # build header
        if tree[cur_idx].op == "START":
            self._write_header(tree[cur_idx].label)
            cur_idx += 1
        else:
            self._write_header()
        # build text
        code_buffer = ""
        base = locctr = buffer_begin = self.starting

        while cur_idx < len(tree):
            if tree[cur_idx].op == "END":
                break

            # point to next instruction
            inst_size = self._instruction_size(tree[cur_idx])
            locctr += inst_size
            cur_node = tree[cur_idx]

            cur_idx += 1

            # gen code
            if cur_node.type == InstructionType.SIC:
                cur_code = self._gen_instruction(cur_node, locctr, base)
            elif cur_node.op == "WORD":
                # TODO: check this
                cur_code = "{:06X}".format(int(cur_node.operand[0]))
            elif cur_node.op == "RESB" or cur_node.op == "RESW":
                # force flush
                self._write_code(buffer_begin, code_buffer)
                buffer_begin = locctr
                code_buffer = ""
                continue
            elif cur_node.op == "BYTE":
                if cur_node.operand[0][0] == "X":
                    cur_code = cur_node.operand[0][2:-1]
                elif cur_node.operand[0][0] == "C":
                    cur_code = self._char_2_byte(cur_node.operand[0][2:-1])
            elif cur_node.op == "BASE":
                if cur_node.operand[0] in self.symbol:
                    base = self.symbol[cur_node.operand[0]]
                else:
                    print(f"Undefined symobol: {cur_node.operand[0]}")
                continue
            elif cur_node.op == "NOBASE":
                base = None
                continue


            # check if need to flush code
            # print(cur_node.op, cur_node.operand, cur_code)
            if len(code_buffer + cur_code) <= 60:
                code_buffer += cur_code
            else:
                self._write_code(buffer_begin, code_buffer)
                buffer_begin += int(len(code_buffer) / 2)
                code_buffer = cur_code
        # clear buffer
        self._write_code(buffer_begin, code_buffer)
        buffer_begin = locctr

        # build relocation
        # TODO: finish it

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
