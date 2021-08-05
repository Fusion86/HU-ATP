from smickelscript.compiler import compile_to_asm
from smickelscript.native_helper import assert_environment, run_native


def test_println_string_const():
    assert_environment()

    src = """func main() { println_str("Hello World"); }"""
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "Hello World\n"


def test_odd_even():
    assert_environment()

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
        println_integer(odd(4));
        println_integer(odd(5));
        println_integer(even(4));
        println_integer(even(5));
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "0\n1\n1\n0\n"


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
        println_integer(sommig(5));
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "15\n"


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
        println_integer(sommig(10));
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "55\n"


def test_global_var():
    src = """
    static var a = 5432;

    func b() {
        println_integer(a);
    }

    func main() {
        b();
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "5432\n"


def test_arithmetic_sub():
    src = """
    func main() {
        var a = 5;
        a = a - 1;
        println_integer(a);
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "4\n"


def test_nested_call_hell():
    src = """
    func a(n: number) { return b(n + 1); }
    func b(n: number) { return c(n + 1); }
    func c(n: number) { return d(n + 1); }
    func d(n: number) { return n + 1; }

    func main() {
        println_integer(a(4));
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "8\n"


def test_set_array():
    src = """
    func main() {
        static var a: array[100];
        a[40] = "H";
        a[41] = "e";
        a[42] = "l";
        a[43] = "l";
        a[44] = "o";
        a[45] = "\\n";

        var i: number = 40;
        while (i <= 45) {
            print_int_as_char(a[i]);
            i = i + 1;
        }
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "Hello\n"


def test_array_len():
    src = """
    func array_length() {
        var len: number = 0;
        while (true) {
            # We can't inline the 'a[len]' line in the condition, because this language is shit.
            var c = a[len];
            if (c == 0) {
                return len;
            }
            len = len + 1;
        }
    }

    func main() {
        static var a: array[300] = "Hello world";
        println_integer(array_length());
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "11\n"


def test_var_inside_while():
    src = """
    func main()
    {
        var a = 0;
        while (a < 10) {
            var b = 0;
            a = a + 1;
            print_str("-");
        }
        println_str("");
    }
    """
    asm = compile_to_asm(src)
    output = run_native(asm)
    assert output == "----------\n"
