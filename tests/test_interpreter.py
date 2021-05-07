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
