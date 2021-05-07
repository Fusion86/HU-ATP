import pytest
from smickelscript import lexer, parser


def parse(code: str):
    return parser.parse_tokens(lexer.tokenize_str(code))


def test_empty():
    tokens = parse("")
    assert tokens == []


def test_comments():
    src = """
    // This is a comment.
    # This also is a comment.
    """
    ast = parse(src)
    assert len(list(map(type, ast))) == 2


def test_hello_world():
    src = """
    func main() {
        println("Hello World");
    }
    """
    ast = parse(src)
    assert ast == [
        parser.FunctionToken(
            lexer.IdentifierToken(2, "main"),
            [],
            lexer.TypeToken(2, "void"),
            parser.ScopeWithBody(
                [
                    parser.FuncCallToken(
                        lexer.IdentifierToken(3, "println"),
                        [parser.LiteralToken(lexer.StringLiteralToken(3, "Hello World"))],
                    )
                ]
            ),
        )
    ]


def test_variable_assignment():
    src = "var a = 1;"
    ast = parse(src)


def test_variable_assignment_math():
    # This is not supported.
    src = "var a = 1 + 2;"

    with pytest.raises(parser.UnexpectedTokenException):
        ast = parse(src)


def test_arithmetic():
    src = "var a = 1; a = a + 1;"
    ast = parse(src)


def test_variable_move():
    src = "var a = 1; var b = a;"
    ast = parse(src)


def test_variable_move():
    src = """
    var b: number = "Hello world";

    func hello(txt: string) { println(txt); }
    hello(b);
    """
    ast = parse(src)


def test_invalid_func():
    # No opening and closing brackets, {}
    src = "func hello(txt: string) println(txt);"
    with pytest.raises(parser.UnexpectedTokenException):
        ast = parse(src)


def test_multi_scope():
    src = """
    func main() {
        var a = "Initial";
        println(a);
        {
            var a = "Second";
            println(a);
        }
        {
            var a = "Third";
            println(a);
        }
        println(a);
    }
    """
    ast = parse(src)
    pass
