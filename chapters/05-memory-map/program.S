    .section .text
    .globl _start
_start:
    lui   t0, 1
    addi  t0, t0, -4           # Final ROM word 0x00000ffc
    lw    t1, 0(t0)
    li    t2, 0x5a6b7c8d      # The initialized ROM boundary word must match.
    bne   t1, t2, fail
    addi  t0, zero, 0          # First ROM word 0x00000000
    lw    t1, 0(t0)
    li    t2, 0x000012b7      # Machine code for the first lui t0,1 instruction
    bne   t1, t2, fail

    lui   t0, 0x10             # First SRAM word in the hand-built SoC: 0x00010000
    lui   t1, 0x12345
    addi  t1, t1, 0x678        # 0x12345678
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    bne   t1, t2, fail
    lui   t0, 0x11
    addi  t0, t0, -4           # Final SRAM word in the hand-built SoC: 0x00010ffc
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    bne   t1, t2, fail

    lui   t0, 0x20000          # First register address in the hand-built SoC: 0x20000000
    lui   t1, 0x2468a
    addi  t1, t1, 0x135        # 0x2468a135
    sw    t1, 0(t0)
    lw    t2, 0(t0)
    bne   t1, t2, fail         # The first register word must also read back correctly
#ifndef UNMAPPED_CASE
    addi  t3, zero, 0x5a
    lui   t0, 0x20001
    addi  t0, t0, -4           # Final endpoint word in the hand-built SoC: 0x20000ffc
    sw    t3, 0(t0)             # The final register also acts as the completion endpoint
#else
    lui   t0, 0x30000          # Address 0x30000000 is intentionally unmapped
    lw    t1, 0(t0)            # Unmapped access; no completion write should occur
#endif
1:  jal   zero, 1b
fail:
    jal   zero, fail
