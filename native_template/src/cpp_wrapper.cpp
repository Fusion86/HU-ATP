#include <Arduino.h>

extern "C" {
    void serial_begin() {
        Serial.begin(9600);
    }

    void print_str(const char* str) {
        Serial.print(str);
    }

    void println_str(const char* str) {
        Serial.println(str);
    }

    void print_integer(int i) {
        Serial.print(i);
    }

    void println_integer(int i) {
        Serial.println(i);
    }

    void print_int_as_char(int i) {
        Serial.print((char)i);
    }

    int smickelscript_rand(int i) {
        return random(i);
    }

    void smickelscript_entry();
}
