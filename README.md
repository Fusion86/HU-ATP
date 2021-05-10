# SmickelScript

Crappy programming language made for a school assignment. Heavily influenced by JavaScript/TypeScript.
We had to use functional functions, which sometimes suck in Python. So the code might not always be readable.

## Features

- Three builtin types: string, number and void
- Two builtin functions: print and println
- Custom functions with parameters using the `func` keyword
- If statements
- While loops
- Scoped variables, with the option to update a var in a 'parent' scope
- Basic CLI interface (using `python -m smickelscript.cli`)

## TODO

Some things which could be improved. The language is "Jan-Complete" at the moment, which means that it should be enough to pass the course.

- [required] Add typing where missing
- [required] Add docstrings
- Better debugging (trace call stack? trace state changes?)
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
python -m smickelscript.cli exec -i example/multiple_args.sc Wouter "How are you?"

# Or call a different entry point
python -m smickelscript.cli exec -i example/test.sc -e sommig 5
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
