func main() {
    {
        var a = "First";
        println(a);
    }
    {
        var a = "Second";
        println(a);
    }
    // This will throw an "Undefined variable" error.
    println(a);
}