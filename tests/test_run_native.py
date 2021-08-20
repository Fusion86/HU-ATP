from smickelscript.compiler import compile_src
from smickelscript.native_helper import assert_environment, run_native


def test_println_string_const():
    src = """func main() { println_str("Hello World"); }"""
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "Hello World\n"


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
    asm = compile_src(src)
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
    asm = compile_src(src)
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
    asm = compile_src(src)
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
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "4\n"


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
    output = run_native(asm)
    assert output == "10\n5\n2\n1\n0\n"


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
    asm = compile_src(src)
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
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "11\n"


def test_array_dynamic_insert():
    src = """
    func main() {
        static var a: array[20];
        var i = 0;

        # Dynamically init array
        while (i < 20) {
            a[i] = 1;
            i = i + 1;
        }

        # Sum array
        i = 0;
        var sum = 0;
        while (i < 20) {
            var tmp = a[i];
            sum = sum + tmp;
            i = i + 1;
        }

        println_integer(sum);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "20\n"


def test_var_inside_while():
    src = """
    func main()
    {
        var a = 0;
        while (a < 4) {
            var b = 0;
            b = b + 1;
            a = a + 1;
            println_integer(b);
        }
        println_integer(a);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "1\n1\n1\n1\n4\n"


def test_var_inside_while_access_outside():
    src = """
    func main()
    {
        var a = 0;
        if (a != 0) {
            var b = 5;
        }
        if (a == 0) {
            var b = 10;
        }
        println_integer(b);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "10\n"


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
        println_integer(odd);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "1\n"


def test_rust_return():
    src = """
    func sommig(n: number): bool {
        var result = 0
        while (n >= 1) {
            result = result + n
            n = n - 1
        }
        result
    }    
    
    func main()
    {
        println_integer(sommig(5));
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "15\n"


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
    output = run_native(asm)
    assert output == "10\n5120\n"


def test_static_var_init():
    src = """
    func init() {
        return 10;
    }

    func main()
    {
        static var a = init();
        println_integer(a);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "10\n"


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
    output = run_native(asm)
    assert output == "128\n256\n512\n1024\n16384\n524288\n"


def test_arduino_delay():
    src = """
    func main()
    {
        println_str("Hello");
        delay(1000);
        println_str("World");
    }
    """
    asm = compile_src(src)
    run_native(asm)


def test_get_time():
    src = """
    func main()
    {
        var t = time();
        println_integer(t);
        delay(1234);  
        println_integer(time_ms());
    }
    """
    asm = compile_src(src)
    run_native(asm)


def test_empty_function_bug():
    src = """
    func noop() { }

    func main()
    {
        println_str("Hello");
        noop();
        println_str("World");
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "Hello\nWorld\n"


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

        a = 5;
        if (a == 4) {
            println_str("if");
        } else {
            println_str("else");
        }
        println_str("end");
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "if\nelse\nend\n"


def test_modulo():
    src = """
    func main()
    {
        var a = 5;
        var b = 0;
        b = a % 2;
        println_integer(b);
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == "1\n"

def test_array_insert_dynamic_value():
    src = """
    static var a: array[1];

    func main()
    {
        # You CAN NOT use ";", because that will store the pointer to the string in the array.
        str(59);
        print_int_as_char(a[0]);
        println_str("");
    }

    func str(x) {
        a[0] = x;
    }
    """
    asm = compile_src(src)
    output = run_native(asm)
    assert output == ";\n"
