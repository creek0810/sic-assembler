import sys

from codeGen import CodeGen

from sicParser import SicParser


if __name__ == "__main__":
    arg = sys.argv
    if len(arg) != 2:
        print("Please enter the file path")
    else:
        # parse
        parser = SicParser(arg[1])
        tree = parser.parse()
        # gen
        generator = CodeGen(arg[1])
        generator.gen(tree)
