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

    int smickelscript_time() {
        return millis() / 1000;
    }

    int smickelscript_time_ms() {
        return millis();
    }

    int smickelscript_modulo(int a, int b) {
        // This could also be implemented in ASM using a repeated subtraction loop.
        // But I don't want to butcher the performance for code using the modulo operator.
        return a % b;
    }
}
