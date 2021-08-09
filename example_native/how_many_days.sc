    static var div_a = 0;
    static var div_b = 0;

    func division(): number {
        var c: number = 0;
        div_a = div_a - div_b;
        while (div_a >= 0) {
            div_a = div_a - div_b;
            c = c + 1;
        }
        return c;
    }

func main() {
    // Hardcode func parameters because we can't pass those when compiling for Arduino.
    static var year = 1998;
    static var month = 11;
    static var day = 16;

    // Hardcode the current date, because there is no way to get the current date.
    static var now_day = 17;
    static var now_month = 5;
    static var now_year = 2021;

    static var years_old = 0;
    years_old = now_year - year;

    static var years_days_old = 0;
    years_days_old = years_old * 365;

    // Approximate leap years
    div_a = years_old;
    div_b = 4;
    var div = division();
    years_days_old = years_days_old + div;

    static var months_old = 0;
    months_old = now_month - month;

    static var months_days_old = 0;
    months_days_old = months_old * 30;

    // Approximate uneven months
    div_a = months_old;
    div_b = 2;
    div = division();
    div = div - 2; // Hacky way to account for february
    months_days_old = months_days_old + div;

    static var days_old = 0;
    days_old = now_day - day;

    var days: number = 0;
    days = days + years_days_old;
    days = days + months_days_old;
    days = days + days_old;

    print_str("You are approximately ");
    print_integer(days);
    println_str(" days old.");
}
