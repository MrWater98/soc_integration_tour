    .section .text.init
    .globl _start
_start:
    csrci mstatus, 8
    csrr a0, mhartid
    la sp, __stack_top
    slli t0, a0, 11
    sub sp, sp, t0
    la t0, trap_entry
    csrw mtvec, t0
    call main
1:  j 1b

    .align 2
trap_entry:
    addi sp, sp, -64
    sw ra, 60(sp)
    sw t0, 56(sp)
    sw t1, 52(sp)
    sw t2, 48(sp)
    sw a0, 44(sp)
    sw a1, 40(sp)
    sw a2, 36(sp)
    sw a3, 32(sp)
    sw a4, 28(sp)
    sw a5, 24(sp)
    sw a6, 20(sp)
    sw a7, 16(sp)
    sw t3, 12(sp)
    sw t4, 8(sp)
    sw t5, 4(sp)
    sw t6, 0(sp)
    call isr
    lw ra, 60(sp)
    lw t0, 56(sp)
    lw t1, 52(sp)
    lw t2, 48(sp)
    lw a0, 44(sp)
    lw a1, 40(sp)
    lw a2, 36(sp)
    lw a3, 32(sp)
    lw a4, 28(sp)
    lw a5, 24(sp)
    lw a6, 20(sp)
    lw a7, 16(sp)
    lw t3, 12(sp)
    lw t4, 8(sp)
    lw t5, 4(sp)
    lw t6, 0(sp)
    addi sp, sp, 64
    mret
