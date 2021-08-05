import os
import sys
import subprocess
from threading import Thread
from queue import Queue, Empty
from subprocess import PIPE, STDOUT
from smickelscript.compiler import compile_to_asm


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


def run_native(code):
    # Based on https://stackoverflow.com/a/4896288/2125072

    def enqueue_output(out, queue):
        for line in iter(out.readline, b""):
            queue.put(line)
        out.close()

    root = os.path.dirname(os.path.realpath(__file__))
    cwd = os.path.join(root, "..", "native_template")

    dump_code(code, os.path.join(cwd, "src", "codegen.s"))

    cmd = "pio run --target upload --target monitor --environment due"
    process = subprocess.Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=cwd)
    q = Queue()
    t = Thread(target=enqueue_output, args=(process.stdout, q))
    t.daemon = True
    t.start()

    started = False
    finished = False
    output = ""

    with open("native.log", "w") as f:
        while True:
            try:
                line = q.get(timeout=5)
            except Empty:
                print("No output within timeout, exiting.")
                break
            else:
                line = line.decode("utf-8").replace("\r", "")
                sys.stdout.write(line)
                f.write(line)
                f.flush()

                if line == "> Finished\n":
                    finished = True
                    break
                elif started:
                    output += line
                elif line == "> Executing smickelscript_entry\n":
                    started = True
                elif "No device found on" in line:
                    raise Exception(line)

    process.terminate()
    process.wait()

    assert started, "Program never started"
    assert finished, "Program never finished"
    return output


def compile_asm(asm):
    root = os.path.dirname(os.path.realpath(__file__))
    cwd = os.path.join(root, "..", "native_template")

    dump_code(asm, os.path.join(cwd, "src", "codegen.s"))
    subprocess.check_output(["pio", "run", "--environment", "due"], cwd=cwd)
