# SmickelScript

Crappy programming language made for a school assignment. Heavily influenced by JavaScript/TypeScript.

## TODO

- [required] Allow interpreter to pass arguments to the entry point (e.g. main or own func)
- Better error message when a function is missing a return statement (but a return typehint is given)
- Print statement without newline?
- Some interesting example code

## Numbers

If a negative sign 'touches' a number it will always be interpreted as a negative number.
E.g `var a = 1 -1` is NOT the same as `var a = 1 - 1`.
The first example is invalid code, and the second is valid code.

## Scope

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

## Types

All typehints are optional, but when they are given they will be enforced. If the typehints are omitted they will be guessed.
