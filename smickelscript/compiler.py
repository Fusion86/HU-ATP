from typing import List, TypeVar, Tuple, Type, Optional, Callable
from smickelscript import lexer, parser


class SmickelCompilerException(Exception):
    """Generic compiler exception."""

    pass


def compile_source(source: str):
    return compile(parser.load_source(source))


def compile(ast: List[parser.ParserToken], statement: parser.ParserToken = None, state=None):
    if statement == None:
        if not ast or len(ast) < 0:
            raise SmickelCompilerException("No AST")
        statement = ast[0]

    if state == None:
        pass  # TODO

    statement_type = type(statement)
    if statement_type in token_compilers:
        src, state = token_compilers[statement_type](ast, statement, state)
    else:
        raise NotImplementedError(
            "Statement {} is not implemented.".format(statement_type.__name__)
        )


def compile_func(ast: List[parser.ParserToken], statement: parser.FunctionToken = None):
    raise ""


token_compilers = {
    parser.FunctionToken: compile_func,
}

if __name__ == "__main__":
    compile_source("""func main() { println("Hello World"); }""")
