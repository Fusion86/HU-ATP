func get_item(i: number) {
    if (i == 0) {
        return a;
    }

    if (i == 1) {
        return b;
    }

    if (i == 2) {
        return c;
    }
}

func set_item(i: number, value: number) {
    if (i == 0) {
        a = value;
    }

    if (i == 1) {
        b = value;
    }

    if (i == 2) {
        c = value;
    }
}

func main() 
{
    var max: number = 3;
    var a: number = 0;
    var b: number = 0;
    var c: number = 0;
    var i: number = 0;
    var temp: number = 0;

    // Set array
    while (i < max) {
        temp = i + 42;
        set_item(i, temp);
        i = i + 1;
    }

    // Print array
    i = 0;
    while (i < max) {
        println(get_item(i));
        i = i + 1;
    }
}
