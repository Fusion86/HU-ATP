from smickelscript.interpreter import run_source


def run_capture_stdout(src: str):
    captured_output = ""

    def stdout_cap(x):
        nonlocal captured_output
        captured_output = captured_output + x

    run_source(src, stdout=stdout_cap)
    return captured_output
