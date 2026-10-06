    .section .text.init
    .globl _start
_start:
    la sp, __stack_top
    la t0, trap_entry
    csrw mtvec, t0
    li t0, 0x800             # VexRiscv accepts LiteX IRQ sources as machine external interrupts.
    csrw mie, t0
    la t0, __data_load_start
    la t1, __data_start
    la t2, __data_end
1:  bgeu t1, t2, 2f
    lw t3, 0(t0)
    sw t3, 0(t1)
    addi t0, t0, 4
    addi t1, t1, 4
    j 1b
2:  la t1, __bss_start
    la t2, __bss_end
3:  bgeu t1, t2, 4f
    sw zero, 0(t1)
    addi t1, t1, 4
    j 3b
4:  call main
5:  j 5b

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
