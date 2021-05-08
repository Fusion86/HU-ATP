import pytest
from typing import List
from smickelscript import lexer, parser, interpreter
from smickelscript.interpreter import run_source


def run_capture_stdout(src: str):
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    run_source(src, stdout=stdout_cap)
    return captured_output


def test_odd_even():
    src = """
    func odd(n: number): bool {
        if(n == 0) { return false; }
        return even(n - 1);
    }

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
    assert run_capture_stdout(src) == "false\ntrue\ntrue\nfalse\n"


def test_sommig_5():
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
    assert run_capture_stdout(src) == "15\n"


def test_sommig_10():
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
        println(sommig(10));
    }
    """
    assert run_capture_stdout(src) == "55\n"
