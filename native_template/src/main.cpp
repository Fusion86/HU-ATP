#include <Arduino.h>

extern "C" {
    void smickel_print(const char* str) {
        Serial.print(str);
    }

    void smickel_println(const char* str) {
        Serial.println(str);
    }

    void smickelscript_entry();
}

void setup() {
    Serial.begin(9600);

    smickelscript_entry();
}

void loop() {}
