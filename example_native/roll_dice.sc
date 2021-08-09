func main() {
    var count = 4;
    while (count > 0) {
        count = count - 1;
        print_str("Rolled a: ");
        var res = rand(6);
        res = res + 1; # +1 because rand returns 0-5
        println_integer(res);
    }
}
