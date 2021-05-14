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


def test_brainfuck():
    src = """
    func array_length(a: array) {
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
        var program: array[300] = "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.";
        var cells: array[30000];
        var op_ptr: number = 0;
        var cell_ptr : number = 0;

        var len = array_length(program);
        //print("Program length: ");
        //println(len);

        while (op_ptr < len) {
            var command = program[op_ptr];

            if (command == ">") {
                cell_ptr = cell_ptr + 1;
            }

            if (command == "<") {
                cell_ptr = cell_ptr - 1;
            }

            if (command == "+") {
                var t = cells[cell_ptr];
                t = t + 1;

                if (t > 255) {
                    t = 0;
                }

                cells[cell_ptr] = t;
            }

            if (command == "-") {
                var t = cells[cell_ptr];
                t = t - 1;

                if (t < 0) {
                    t = 255;
                }

                cells[cell_ptr] = t;
            }

            if (command == ".") {
                print(cells[cell_ptr]);
            }
            
            // command == "," is not supported, because we don't have a stdin

            if (command == "[") {
                var t = cells[cell_ptr];
                if (t == 0) {
                    # Not implemented
                    return 1;
                }
            }

            if (command == "]") {
                var t = cells[cell_ptr];
                if (t != 0) {
                    # Not implemented
                    return 1;
                }
            }

            op_ptr = op_ptr + 1;
        }
    }
    """
    assert run_capture_stdout(src) == "Hello World!"
