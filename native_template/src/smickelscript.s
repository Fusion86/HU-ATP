.cpu cortex-m0
.align 2

.data

lit_0:
  .asciz "Hello World"

.text
.global smickelscript_entry

smickelscript_entry:
  push { r4, r5, r6, lr }
  ldr r0, =lit_0
  bl println
  pop { r4, r5, r6, pc }
