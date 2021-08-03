import os
import sys
import signal
import subprocess
from threading import Thread
from queue import Queue, Empty
from subprocess import PIPE, STDOUT
from smickelscript.compiler import compile_source


def dump_code(code, dst="dump_code.s"):
    with open(dst, "w") as f:
        f.write(code)


def assert_environment():
    # Check if pio is installed
    try:
        subprocess.call(["pio"])
    except FileNotFoundError:
        raise Exception("PlatformIO not found.")

    pio_device_list_output = subprocess.check_output(["pio", "device", "list"]).decode("utf-8")
    if "Description: Arduino" not in pio_device_list_output:
        raise Exception("No Arduino microcontroller connected.")


def run_assembler_and_linker(code):
    root = os.path.dirname(os.path.realpath(__file__))
    cwd = os.path.join(root, "..", "native_template")

    dump_code(code, os.path.join(cwd, "src", "codegen.s"))
    subprocess.check_output(["pio", "run", "--environment", "due"], cwd=cwd)


def test_println_string_const():
    assert_environment()

    src = """func main() { println_str("Hello World"); }"""
    asm = compile_source(src)
    run_assembler_and_linker(asm)


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
    asm = compile_source(src)
    run_assembler_and_linker(asm)


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
    asm = compile_source(src)
    run_assembler_and_linker(asm)


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
    asm = compile_source(src)
    run_assembler_and_linker(asm)
