from codeGen import CodeGen

from sicParser import SicParser


# from pass1 import pass1
if __name__ == "__main__":
    # parse
    parser = SicParser("../tests/in/sicxe.asm")
    tree = parser.parse()
    # gen
    generator = CodeGen()
    generator.gen(tree)
