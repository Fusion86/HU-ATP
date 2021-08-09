# This doesn't work too well on the actual Arduino because we lack 'randomness'.

func main() {
    var max = 600;
    var r = 1;

    while (r != 0) {
        r = rand(max);
        println_str("To infinity!");
    }
}
