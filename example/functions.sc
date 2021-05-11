func odd(n:number):bool {
    if(n==0) { return false; }
    return even(n - 1);
}

func even(n: number): bool {
    if (n == 0) { return true; }
    // We even support rust-like implicit returns.
    odd(n - 1);
}

// Semicolons usually aren't required.
func sommig(n: number): bool {
    var result = 0
    while (n >= 1) {
        result = result + n
        n = n - 1
    }
    result
}

func main(): void {
    // Variables don't clash with functions.
    var odd = odd(5);
    print("5 is an odd number: ");
    println(odd);
    print("6 is an odd number: ");
    println(odd(6));
    println("Try calling the functions 'odd', 'even' or 'sommig' using the interpreter's '-e' option.");
}
