    .section .text
    .globl _start
_start:
    lui   t0, 1
    addi  t0, t0, -4           # Final ROM word 0x00000ffc
    lw    t1, 0(t0)
    li    t2, 0x5a6b7c8d      # The initialized ROM boundary word must match.
    li    t4, 1
    bne   t1, t2, fail
    addi  t0, zero, 0          # First ROM word 0x00000000
    lw    t1, 0(t0)
    li    t2, 0x000012b7      # Machine code for the first lui t0,1 instruction
    li    t4, 2
    bne   t1, t2, fail

    lui   t0, 0x10000          # First LiteX VexRiscv SRAM word 0x10000000
    lui   t1, 0x12345
    addi  t1, t1, 0x678        # 0x12345678
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    li    t4, 3
    bne   t1, t2, fail
    lui   t0, 0x10001
    addi  t0, t0, -4           # Final LiteX SRAM word 0x10000ffc
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    li    t4, 4
    bne   t1, t2, fail

    lui   t0, 0x80000          # Test register in the LiteX VexRiscv IO window
    lui   t1, 0x2468a
    addi  t1, t1, 0x135        # 0x2468a135
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    li    t4, 5
    bne   t1, t2, fail         # The first register word must also read back correctly
    addi  t3, zero, 0x5a
    lui   t0, 0x80001
    addi  t0, t0, -4           # Final word in the LiteX IO test region 0x80000ffc
    sw    t3, 0(t0)             # The final register also acts as the completion endpoint
1:  jal   zero, 1b
fail:
    lui   t0, 0x80000
    sw    t2, 8(t0)
    addi  t3, t4, 0xe0
    lui   t0, 0x80001
    addi  t0, t0, -4
    sw    t3, 0(t0)
    jal   zero, fail
