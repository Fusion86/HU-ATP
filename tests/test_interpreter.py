import pytest
from smickelscript import lexer, parser, interpreter
from smickelscript.interpreter import run_source
from helper import run_capture_stdout


def test_empty():
    src = ""
    with pytest.raises(interpreter.EntrypointNotFoundException):
        run_source(src)


def test_undefined_variable():
    src = "func main() { println(a); }"
    with pytest.raises(interpreter.UndefinedVariableException):
        run_source(src)


def test_var_assignment():
    src = "func main() { var a = 1; }"
    run_source(src)



def test_arithmetic_sub():
    src = """
    func main() {
        var a = 5;
        a = a - 1;
        println(a);
    }
    """
    assert run_capture_stdout(src) == "4\n"


def test_arithmetic_add_negative_no_space():
    src = """
    func main() {
        var a = 5;
        a = a + -1;
        println(a);
    }
    """
    assert run_capture_stdout(src) == "4\n"


def test_arithmetic_sub_negative():
    src = """
    func main() {
        var a = 5;
        a = a--1;
        println(a);
    }
    """
    assert run_capture_stdout(src) == "6\n"


def test_multi_scope():
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
    assert run_capture_stdout(src) == "First\nSecond\nRoot\nRoot\n"


def test_increment_in_parent_scope():
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
    assert run_capture_stdout(src) == "10\n"


def test_increment_in_scope():
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
    assert run_capture_stdout(src) == "incr_a:\n10\nmain:\n0\n"


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


def test_return_bool_var():
    src = """
    func main() { var a: bool = true; return a; }
    """
    run_source(src)


def test_return_bool_literal():
    src = """
    func main() { return true; }
    """
    run_source(src)


def test_invalid_type():
    src = """
    func test(a: number) { }
    func main() { test("String type"); }
    """
    with pytest.raises(interpreter.InvalidTypeException):
        run_source(src)


def test_no_func_type():
    src = """
    func test(a) { }
    func main() { println(test("String type")); }
    """


def test_odd_even():
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
    assert run_capture_stdout(src) == "false\ntrue\ntrue\nfalse\n"


def test_string_concat():
    src = """
    func main() {
        var a = "Hello";
        a = a + " ";
        a = a + "World";
        println(a);
    }
    """
    assert run_capture_stdout(src) == "Hello World\n"



def test_exit_code():
    src = "func main() { return 1; }"
    res = run_source(src)
    assert res == 1


def test_exit_value():
    src = 'func main() { return "Hello"; }'
    res = run_source(src)
    assert res == "Hello"


def test_return_type():
    src = 'func main(): string { return "Hello"; }'
    run_source(src)


def test_invalid_return_type():
    src = 'func main(): number { return "Hello"; }'
    with pytest.raises(interpreter.InvalidTypeException):
        run_source(src)


def test_main_void():
    src = "func main(): void { }"
    run_source(src)


def test_main_number_no_return():
    src = "func main(): number { }"
    with pytest.raises(interpreter.InvalidTypeException):
        run_source(src)


def test_func_call_2_params():
    src = """
    func hello(a: string, b: string): string {
        return "Sup";
    }

    func main() {
        println(hello("Hello", "World"));
    }
    """
    assert run_capture_stdout(src) == "Sup\n"


def test_implicit_number_return():
    src = """
    func add(a: number, b: number) {
        a + b;
    }

    func main() {
        println(add(5, 6));
    }
    """
    assert run_capture_stdout(src) == "11\n"


def test_implicit_string_return():
    src = """
    func hello(): string {
        "Hello";
    }

    func main() {
        println(hello());
    }
    """
    assert run_capture_stdout(src) == "Hello\n"


def test_invalid_implicit_string_return():
    src = """
    func hello(): string {
        "Hello";
        "World";
    }

    func main() {
        println(hello());
    }
    """
    with pytest.raises(interpreter.InvalidImplicitReturnException):
        run_source(src)


def test_init_void_var():
    src = """
    func main() {
        var a: void;
    }
    """
    with pytest.raises(interpreter.IllegalTypeException):
        run_source(src)


def test_assign_void_var():
    src = """
    func main() {
        var a: void = 3;
    }
    """
    with pytest.raises(interpreter.IllegalTypeException):
        run_source(src)


def test_string_literal_typing():
    src = """
    func main() {
        var a: number = "1\";
    }
    """
    with pytest.raises(interpreter.InvalidTypeException):
        run_source(src)


def test_nested_call_hell():
    src = """
    func a(n: number) { return b(n + 1); }
    func b(n: number) { return c(n + 1); }
    func c(n: number) { return d(n + 1); }
    func d(n: number) { return n + 1; }

    func main() {
        print(a(4));
    }
    """
    assert run_capture_stdout(src) == "8"


def test_duplicate_func():
    src = """
    func a(n: number) { }
    func a(n: number) { }

    func main() {
        a(4);
    }
    """
    with pytest.raises(interpreter.SmickelRuntimeException):
        run_source(src)
