#include <Arduino.h>

extern "C" {
    void print_str(const char* str) {
        Serial.print(str);
    }

    void println_str(const char* str) {
        Serial.println(str);
    }

    void println_integer(int i) {
        Serial.println(i);
    }

    void print_int_as_char(int i) {
        Serial.print((char)i);
    }

    void smickelscript_entry();
}

void setup() {
    Serial.begin(9600);

    Serial.println("> Executing smickelscript_entry");
    smickelscript_entry();
    Serial.println("> Finished");
}

void loop() {}
