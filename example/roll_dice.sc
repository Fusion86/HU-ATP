func main(count: number) {
    while (count > 0) {
        count = count - 1;
        print("Rolled a: ");
        println(rand(6));
    }
}