# SmickelScript

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
