func main(max: number) {
    var r = rand();
    while (r != 0) {
        r = rand(max);
        println("To infinity!");
    }
}