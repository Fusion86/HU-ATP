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
    assert ast[0].static == False


def test_variable_assignment_math():
    src = "var a = 1 + 2;"
    ast = parse(src)


def test_arithmetic():
    src = "var a = 1; a = a + 1;"
    ast = parse(src)


def test_variable_move():
    src = "var a = 1; var b = a;"
    ast = parse(src)


def test_string_statement():
    src = """
    // The string constant 'returns itself' when executed, 
    // when this is not printed or assigned to a variable nothing happens.
    func main() { "String type"; }
    """
    ast = parse(src)


def test_number_statement():
    src = "1;"
    ast = parse(src)


def test_bool_statement():
    src = "true;"
    ast = parse(src)


def test_comparison_statement():
    src = "true == false;"
    ast = parse(src)


def test_arithmetic_statement():
    src = "2 + 4;"
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


def test_str_index():
    src = """
    func main() {
        var a: string = "Hello World";
        println(a[4]);
    }
    """
    ast = parse(src)


def test_str_dynamic_index():
    src = """
    func main() {
        var a: string = "Hello World";
        var i: number = 3
        println(a[i]);
    }
    """
    ast = parse(src)


def test_init_array():
    src = """
    func main() {
        var a: array[100];
    }
    """
    ast = parse(src)


def test_init_array_with_value():
    src = """
    func main() {
        var a: array[100] = "[->+<]";
    }
    """
    ast = parse(src)


def test_access_array():
    src = """
    func main() {
        var a: array[100];
        println(a[40]);
    }
    """
    ast = parse(src)


def test_dynamic_array_error():
    # This is currently not supported, and therefor should throw an error.
    src = """
    func main() {
        var size: number = 10;
        var a: array[size];
    }
    """
    with pytest.raises(parser.UnexpectedTokenException):
        ast = parse(src)


def test_global_var():
    src = "static var a = 5;"
    ast = parse(src)
    assert ast[0].static == True
