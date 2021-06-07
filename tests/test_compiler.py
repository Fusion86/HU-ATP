from smickelscript.compiler import compile_source


def test_println_string_const():
    src = """func main() { println("Hello World"); }"""
    compile_source(src)
