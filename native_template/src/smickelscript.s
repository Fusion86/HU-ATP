.cpu cortex-m0
.align 2

.data

message:
	.asciz "Hello, ARM!\n"

.text
.global smickelscript_entry

smickelscript_entry:
	push { r4, r5, r6, lr }

	# Print hello world
	ldr r0, =message
	BL smickel_print

	pop { r4, r5, r6, pc }
