func division(a: number, b: number): number {
    var c: number = 0;
    a = a - b;
    while (a >= 0) {
        a = a - b;
        c = c + 1;
    }
    return c;
}

func main(year: number, month: number, day: number) {
    // Hardcode the current date, because there is no way to get the current date.
    var now_day = 12;
    var now_month = 5;
    var now_year = 2021;

    var years_old = 0;
    years_old = now_year - year;

    var years_days_old = 0;
    years_days_old = years_old * 365;

    // Approximate leap years
    var div = division(years_old, 4);
    years_days_old = years_days_old + div;

    var months_old = 0;
    months_old = now_month - month;

    var months_days_old = 0;
    months_days_old = months_old * 30;

    // Approximate uneven months
    var div = division(months_old, 2);
    div = div - 2; // Hacky way to account for february
    months_days_old = months_days_old + div;

    var days_old = 0;
    days_old = now_day - day;

    var days: number = 0;
    days = days + years_days_old;
    days = days + months_days_old;
    days = days + days_old;

    print("You are approximately ");
    print(days);
    println(" days old.");

    // Return the value as well, because we can.
    days;
}
