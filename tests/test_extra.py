from smickelscript.interpreter import run_source
from helper import run_capture_stdout


def test_var_assignment_arithmetic():
    src = "func main() { var a = 1 + 4; }"
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


def test_arithmetic_assignment_add():
    src = """
    func main() {
        var a = 5;
        a += 10;
        println(a);
    }
    """
    assert run_capture_stdout(src) == "15\n"


def test_arithmetic_assignment_sub():
    src = """
    func main() {
        var a = 5;
        a -= 10;
        println(a);
    }
    """
    assert run_capture_stdout(src) == "-5\n"


def test_arithmetic_statement():
    src = """
    // Or arithmetic statements.
    func main() { 2 + 4; }
    """
    run_source(src)


def test_string_concat_multi():
    src = """
    func main() {
        var a = "Hello";
        a = a + " " + "World";
        println(a);
    }
    """
    assert run_capture_stdout(src) == "Hello World\n"


def test_string_concat_func():
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
    assert run_capture_stdout(src) == "15\n"
