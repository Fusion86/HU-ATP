#include <Arduino.h>

extern "C" {
    void print(const char* str) {
        Serial.print(str);
    }

    void println(const char* str) {
        Serial.println(str);
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
