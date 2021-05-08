import pytest
from typing import List
from smickelscript import lexer, parser, interpreter
from smickelscript.interpreter import run_source


def test_empty():
    src = ""
    with pytest.raises(interpreter.EntrypointNotFoundException):
        run_source(src)


def test_undefined_variable():
    src = "func main() { println(a); }"
    with pytest.raises(interpreter.UndefinedVariableException):
        run_source(src)


def test_multi_scope():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func main() {
        var a = "Root";
        {
            var a = "First";
            println(a);
        }
        {
            var a = "Second";
            println(a);
        }
        {
            println(a);
        }
        println(a);
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "First\nSecond\nRoot\nRoot\n"


def test_increment_in_parent_scope():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func main() {
        var a = 0;
        incr_a();
        // This will print '10'.
        println(a);
    }

    func incr_a() {
        a = a + 1;
        a = a + 9;
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "10\n"


def test_increment_in_scope():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func main() {
        var a = 0;
        incr_a();
        // This will print '0'.
        println("main:");
        println(a);
    }

    func incr_a() {
        var a = 0;
        a = a + 1;
        a = a + 9;
        println("incr_a:");
        println(a);
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "incr_a:\n10\nmain:\n0\n"


def test_string_statement():
    src = """
    // The string constant 'returns itself' when executed, 
    // when this is not printed or assigned to a variable nothing happens.
    func main() { "String type"; }
    """
    run_source(src)


def test_number_statement():
    src = """
    // The same is true for numbers.
    func main() { 1; }
    """
    run_source(src)


def test_bool_statement():
    src = """
    // Or bools.
    func main() { true; }
    """
    run_source(src)


def test_comparison_statement():
    src = """
    // Or conditions.
    func main() { true == false; }
    """
    run_source(src)


def test_return_comparison_statement():
    src = """
    // Or conditions.
    func main() { return true == false; }
    """
    run_source(src)


def test_arithmetic_statement():
    src = """
    // Or arithmetic statements.
    func main() { 2 + 4; }
    """
    run_source(src)


def test_invalid_type():
    src = """
    func test(a: number) { }
    func main() { test("String type"); }
    """
    with pytest.raises(interpreter.InvalidTypeException):
        run_source(src)


def test_odd_even():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func odd(n:number):bool{
    if(n==0){return false;}
    return even(n - 1);}

    func even(n: number): bool {
        if (n == 0) { return true; }
        return odd(n - 1);
    }

    func main() {
        println(odd(4));
        println(odd(5));
        println(even(4));
        println(even(5));
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "false\ntrue\ntrue\nfalse\n"


def test_sommig():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func sommig(n: number): bool {
        var result = 0;
        while (n >= 1) {
            result = result + n;
            n = n - 1;
        }
        return result;
    }

    func main() {
        println(sommig(5));
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "15\n"


def test_string_concat_func():
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    src = """
    func say_hello_to(name: string): string {
        return "Hello " + name;
    }

    func ask(question: string): string {
        return "The computer asks you: " + question;
    }

    func main() {
        println(say_hello_to("Kereltje") + "\\n" + ask("How is the weather?"));
    }
    """
    run_source(src, stdout=stdout_cap)
    assert captured_output == "15\n"
