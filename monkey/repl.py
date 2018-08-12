from typing import IO, List
from . import lexer
from . import parser
from . import evaluator
from . import obj

PROMPT = ">>> "


def start(input: IO, output: IO):
    env = obj.Environment()

    while True:
        print(PROMPT, end="")
        output.flush()
        scanned: str = input.readline()
        if not scanned:
            return

        lex = lexer.Lexer(scanned)
        psr = parser.Parser(lex)

        program = psr.parse()
        if len(psr.errors) > 0:
            print_parser_errors(output, psr.errors)
            continue

        evaluated = evaluator.eval(program, env)

        if evaluated:
            print(str(evaluated), file=output)


def print_parser_errors(output: IO, errors: List[str]):
    for error in errors:
        print(f"\t{error}", file=output)
