# SmickelScript

Crappy programming language made for a school assignment. Heavily influenced by JavaScript/TypeScript.
We had to use functional functions, which sometimes suck in Python. So the code might not always be readable.

## Features

- Five builtin types: number, string, bool, array, and void
- Three builtin functions: print, println, and rand
- Custom functions with parameters using the `func` keyword
- If statements
- While loops
- Scoped variables, with the option to update a var in a 'parent' scope
- Fixed size arrays
- Comments
- Basic CLI interface (using `python -m smickelscript.cli`)

## TODO

Some things which could be improved. The language is "Jan-Complete" at the moment, which means that it should be enough to pass the course.

- Better debugging (trace state changes?)
- Better error message when a function is missing a return statement (but a return typehint is given), see `test_main_number_no_return`
- Some interesting example code

## Usage

```sh
# Install the package
pip install -e .

# Run a script
python -m smickelscript.cli exec -i example/hello_world.sc

# Run a script and pass one argument
python -m smickelscript.cli exec -i example/hello_name.sc Wouter

# Or pass multiple args
python -m smickelscript.cli exec -i example/multi_args.sc Wouter "How are you?"

# Or call a different entry point
python -m smickelscript.cli exec -i example/functions.sc -e sommig 5
```

## About the language

### Numbers

If a negative sign 'touches' a number it will always be interpreted as a negative number.
E.g `var a = 1 -1` is NOT the same as `var a = 1 - 1`.
The first example is invalid code, and the second is valid code.

### Scope

All variables in the stack are readable and writeable by all functions.
For example the following snippet is valid code.

```
func main() {
    var a = 0;
    incr_a();
    // This will print '1'.
    println(a);
}

func incr_a() {
    a = a + 1;
}
```

### Types

All typehints are optional, but when they are given they will be enforced. If the typehints are omitted they will be guessed.
Guessing means that it will try to parse it as a number, and if that doesn't work then it must be a string.

### Interpreter

The interpreter will print all `print` and `println` output to the stdout. It will also print the return value of the entry point function (which may be None).

## Tests

There are 5 files with tests.

- test_lexer tests the basic functionality of the lexer.
- test_parser tests the basic functionality of the parser.
- test_interpreter tests the basic functionality of the interpreter.
- test_must_haves tests the code samples provided by the course.
- test_extra tests a few edge cases which aren't (yet) supported by the language. These are optional.

## Jan-Completeness

The not so interesting part.

### Language features

- If statements (implemented in [interpreter.py line 274](./smickelscript/interpreter.py))
- While loops (implemented in [interpreter.py line 290](./smickelscript/interpreter.py))
- Function calls (implemented in [interpreter.py line 99](./smickelscript/interpreter.py))
  - This includes creating your own functions
  - And calling functions within functions
  - The return value can either be assigned to a variable, or directly printed.
  - See [example/functions.sc](./example/functions.sc)
- Multiple variable scopes (implemented in [interpreter.py line 157](./smickelscript/interpreter.py))

### Requirements

- Classes with inheritance (at the top in [interpreter.py](./smickelscript/interpreter.py), [parser.py](./smickelscript/parser.py) and [lexer.py](./smickelscript/lexer.py))
- Object printing for all classes using JSON and a custom encoder.
- Type annotated
- Uses higher order functions
  - (map functions are just a crappy way to write list comprehensions, change my mind)
  - 2x map + 2x zip in [execute_func](./smickelscript/interpreter.py)
  - reduce in [tokenize_file](./smickelscript/lexer.py) and [tokenize_str](./smickelscript/lexer.py)
  - map a bunch of times inside [test_lexer.py](./tests/test_lexer.py)
  - map inside [cli.py](./smickelscript/cli.py)
  - used `next` in [find_func](./smickelscript/interpreter.py) but I had to remove it to allow for duplicate checking

### Turing completeness

We could write a brainfuck interpreter in this language. Because brainfuck is turing complete it also means that this language is turing complete.
To write a brainfuck interpreter you only needs arrays, conditions and basic math (addition and subtraction), all these features are supported in this language.

### Other functionality

See `statement_exec_map` and `operators_map` at line ~391 inside [interpreter.py](./smickelscript/interpreter.py) for a list of all the implemented functions, and how they are implemented.
