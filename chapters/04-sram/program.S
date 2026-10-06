    .section .text
    .globl _start
_start:
    lui   sp, 0x10             # Stack top 0x10100 is inside even the 256-byte SRAM case.
    addi  sp, sp, 0x100
    jal   ra, work
    lui   t0, 0x20000
    sw    a0, 0(t0)            # Include the SRAM readback value in the completion code
1:  jal   zero, 1b
work:
    addi  sp, sp, -16
    sw    ra, 12(sp)           # Save the caller return address before jal overwrites ra
    jal   ra, exercise_sram
    lw    ra, 12(sp)           # Restore the caller return address
    addi  sp, sp, 16
    jalr  zero, 0(ra)
exercise_sram:
    lui   t1, 0x10             # First SRAM address: 0x10000
    lui   t0, 0x11223
    addi  t0, t0, 0x344        # 0x11223344
    sw    t0, 0(t1)
    addi  t0, zero, 0xaa
    sb    t0, 0(t1)            # Replace the lowest byte with aa
    lui   t0, 0xc
    addi  t0, t0, -0x434       # 0x0000bbcc
    sh    t0, 2(t1)            # Replace the upper two bytes with bbcc
    lw    a0, 0(t1)             # Expected readback: 0xbbcc33aa
    lui   t2, 0x55667
    addi  t2, t2, 0x788        # 0x55667788
    lui   t3, 0x11
    addi  t3, t3, -4            # Final RAM word: 0x10ffc
    sw    t2, 0(t3)
    lw    t4, 0(t3)
    bne   t2, t4, 2f
    jalr  zero, 0(ra)
2:  jal   zero, 2b
