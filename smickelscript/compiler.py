from typing import List, TypeVar, Tuple, Type, Optional, Callable
from smickelscript import lexer, parser


def compile_source(source: str):
    return compile(parser.load_source(source))


def compile(ast: List[parser.ParserToken]):
    pass

if __name__ == "__main__":
    compile_source("""func main() { println("Hello World"); }""")
