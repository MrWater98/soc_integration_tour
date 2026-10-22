# SMP 实测仿真

PASS: real SMP RTL and independent mailbox checks

SMP HART 00000000 count=000003E8 sum=0007A314
SMP HART 00000001 count=000003E8 sum=0007A314
SMP ATOMIC count=000007D0
SMP IRQ PASS
SMP TIMER PASS
SMP PASS harts=00000002
SMP HART 00000000 count=000003E8 sum=0007A314
SMP HART 00000001 count=000003E8 sum=0007A314
SMP ATOMIC count=000007D0
SMP IRQ PASS
SMP TIMER PASS
SMP PASS harts=00000002
PASS SMP RESET_RUNS=2
- tb.sv:20: Verilog $finish
- S i m u l a t i o n   R e p o r t: Verilator 5.034 2025-02-24
- Verilator: $finish at 232ms; walltime 0.758 s; speed 305.929 ms/s
- Verilator: cpu 0.758 s on 1 threads; alloced 89 MB

FPGA 上板：NOT_RUN。
