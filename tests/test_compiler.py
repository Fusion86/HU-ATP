import pytest
from smickelscript import compiler
from smickelscript.compiler import compile_src
from smickelscript.native_helper import compile_asm


def test_println_string_const():
    src = """func main() { println_str("Hello World"); }"""
    asm = compile_src(src)
    compile_asm(asm)


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
    asm = compile_src(src)
    compile_asm(asm)


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
    asm = compile_src(src)
    compile_asm(asm)


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
    asm = compile_src(src)
    compile_asm(asm)


def test_parent_stack_access():
    src = """
    func b() {
        println_integer(a);
    }

    func main() {
        var a = 5;
        b();
    }
    """
    with pytest.raises(compiler.UndefinedVariableException):
        compile_src(src)


def test_global_var():
    src = """
    static var a = 5;

    func b() {
        println_integer(a);
    }

    func main() {
        b();
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_arithmetic_sub():
    src = """
    func main() {
        var a = 5;
        a = a - 1;
        println_integer(a);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_manual_division():
    src = """
    static var a = 0;
    static var b = 0;

    func division(): number {
        var c: number = 0;
        a = a - b;
        while (a >= 0) {
            a = a - b;
            c = c + 1;
        }
        return c;
    }

    func main() {
        a = 10;
        b = 1;
        println_integer(division());
        
        a = 10;
        b = 2;
        println_integer(division());
        
        a = 10;
        b = 5;
        println_integer(division());
        
        a = 10;
        b = 10;
        println_integer(division());
        
        a = 10;
        b = 20;
        println_integer(division());
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


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
    asm = compile_src(src)
    compile_asm(asm)


def test_require_array_static():
    """This is something which could be supported in the future, but isn't for now."""

    src = """
    func main() {
        var a: array[100];
    }
    """
    with pytest.raises(compiler.SmickelCompilerException):
        compile_src(src)


def test_require_main():
    src = ""
    with pytest.raises(compiler.EntrypointNotFoundException):
        compile_src(src)


def test_init_array():
    src = """
    static var a: array[100];
    func main() { }
    """
    asm = compile_src(src)
    compile_asm(asm)


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
        while (i <= 44) {
            print_int_as_char(a[i]);
            i = i + 1;
        }
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_comments():
    src = """
    func main() {
        # Print Hello World on the next line.
        // Another comment.
        println_str("Hello World");
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


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
    asm = compile_src(src)
    compile_asm(asm)


def test_array_dynamic_insert():
    src = """
    func main() {
        static var a: array[20];
        var i = 0;

        while (i < 20) {
            a[i] = 1;
            i = i + i;
        }
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_var_inside_while():
    src = """
    func main()
    {
        var a = 0;
        while (a != 0) {
            var b = 5;
        }
        println_integer(b);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_var_limit():
    src = """
    func main()
    {
        var a = 0;
        var b = 0;
        var c = 0;

        if (a != 0) {
            var d = 0;
            var e = 0;
        }
    }
    """
    with pytest.raises(compiler.SmickelCompilerException):
        compile_src(src)


def test_vars():
    src = """
    func main()
    {
        var a = 0;
        var b = 0;
        var c = 0;

        if (a != 0) {
            var d = 0;
        }
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_init_var_with_func_result():
    src = """
    func odd(n:number):bool {
        if(n==0) { return false; }
        return even(n - 1);
    }

    func even(n: number): bool {
        if (n == 0) { return true; }
        // We even support rust-like implicit returns.
        odd(n - 1);
    }

    func main()
    {
        var odd = odd(5);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_disallow_main_func_with_args():
    src = """
    func main(name: string): void {
        print_str("Hello ");
        println_str(name);
    }
    """
    with pytest.raises(compiler.SmickelCompilerException):
        compile_src(src)


def test_math_mult():
    src = """
    func main()
    {
        var a = 2;
        a = a * 5;
        println_integer(a);
        a = a * 512;
        println_integer(a);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_static_var_init():
    src = """
    func init() {
        return 10;
    }

    func main()
    {
        static var a = init();
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_var_large_numbers():
    src = """
    func main()
    {
        var a = 128;
        println_integer(a);
        a = 256;
        println_integer(a);
        a = 512;
        println_integer(a);
        a = 1024;
        println_integer(a);
        a = 16384;
        println_integer(a);
        a = 524288;
        println_integer(a);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_unk_error_1():
    src = """
    func main()
    {
        var res = rand(6);
        res = res + 1;
        println_integer(res);
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_array_insert_dynamic_value():
    src = """
    static var a: array[1];

    func main()
    {
        str("a");
    }

    func str(x) {
        a[0] = x;
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_if_else():
    src = """
    func main()
    {
        var a = 4;
        if (a == 4) {
            println_str("if");
        } else {
            println_str("else");
        }
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_modulo():
    src = """
    func main()
    {
        var a = 4;
        var b = 0;
        b = a % 2;
    }
    """
    asm = compile_src(src)
    compile_asm(asm)


def test_array_insert_from_var():
    src = """
    func main()
    {
        static var arr: array[10];
        var value = 4;
        arr[0] = value;
    }
    """
    asm = compile_src(src)
    compile_asm(asm)
