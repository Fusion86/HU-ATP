from smickelscript.compiler import compile_source


def dump_code(code):
    with open("dump_code.s", "w") as f:
        f.write(code)


def test_println_string_const():
    src = """func main() { println("Hello World"); }"""
    asm = compile_source(src)
    dump_code(asm)


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
        println_integer(odd(4));
        println_integer(odd(5));
        println_integer(even(4));
        println_integer(even(5));
    }
    """
    asm = compile_source(src)
    dump_code(asm)
