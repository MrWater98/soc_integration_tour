# Same three instructions used by soc.py's fixed startup ROM.
# Chapter 01 needs no cross-compiler; chapter 03 compiles its own program.
    .section .text
    .globl _start
_start:
    addi x1, x0, 64
    sw   x1, 0(x1)
1:  j    1b
