.cpu cortex-m0
.align 2

.data

smickel_executing_str: .asciz "> Executing user code"
smickel_finished_str: .asciz "> Finished"

.text
.global setup, loop

setup:
  mov r4, lr

  @ Init serial connection
  bl serial_begin

  @ Call the function which sets the random seed.
  @ This function is generated in the compiler because it also generates the seed.
  bl smickelscript_codegen_randinit

  @ Print smickel_executing_str
  ldr r0, =smickel_executing_str
  bl println_str

  @ Execute user code
  bl smickelscript_codegen_main

  @ Print smickel_finished_str
  ldr r0, =smickel_finished_str
  bl println_str

  mov pc, r4

loop:
  mov pc, lr
