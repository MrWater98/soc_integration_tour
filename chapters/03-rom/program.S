    .section .text
    .globl _start
_start:
    lui   t0, 0x20000          # Completion register byte address: 0x20000000
    addi  t1, zero, 0x35       # Firmware completion marker: 0x35
    sw    t1, 0(t0)            # CPU completion write through the AXI-Lite bridge
1:  jal   zero, 1b
