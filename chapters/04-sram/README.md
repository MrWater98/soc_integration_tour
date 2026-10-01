# 04 — Writable SRAM, Stack, and the Hardware Behind a Memory Model

Stage 03 had read-only firmware storage. This stage adds a 4 KiB Wishbone SRAM at byte address `0x00010000`. Firmware tests the first and last word, updates individual bytes, and calls a function that saves and restores its return address in SRAM.

## What kind of SRAM is this?

The design uses LiteX's `wishbone.SRAM`, a Migen-described behavioral memory with a Wishbone port. In this simulation, it is part of the generated SoC hardware. There is no separate SystemVerilog `tb.sv` that reimplements the SRAM. The CPU issues bus transactions; LiteX's SRAM module responds to them. This keeps the memory behavior and the interface being tested in the same design.

That model is enough to test address decoding, read/write behavior, byte enables, initialization assumptions, and firmware use of RAM. It does not model a particular chip's analog behavior, setup/hold limits, retention, power, or proprietary timing corners.

### How would this become real FPGA or ASIC SRAM?

An FPGA implementation generally maps an inferred memory or vendor block-RAM primitive into the device's memory resources. The synthesis result and timing report determine whether the memory really became a BRAM and what read latency and write-mask behavior it has. A LiteX simulation memory is not by itself proof of FPGA mapping.

An ASIC SRAM macro is usually a hard memory block supplied by a memory compiler or foundry library. Its pins are typically clock/enable, address, data, write enable or byte mask, and read data. It does not normally speak Wishbone. A wrapper translates Wishbone requests into those pins, handles the macro's latency, and returns ACK or ERR at the right cycle. In a chip verification environment, engineers may use a functional macro model for normal tests and separate timing, power, or physical checks for other properties.

### Why not put the SRAM behavior in a testbench?

This chapter tests the complete LiteX-side path from CPU bus to the SRAM module. Putting the only memory implementation in an external testbench would leave the SoC design without an integrated memory block and could hide a mismatch between the design's memory interface and the test model. A separate testbench model is useful when verifying a wrapper against a vendor macro interface, but it serves a different test boundary. Here LiteX's SRAM module is the target under test.

## Why does the firmware set `sp`?

The stack is ordinary writable RAM reserved for function calls and temporary saved state. The processor does not automatically create a stack frame on a `jal`. Software convention uses register `sp` (`x2`) to mark the current stack allocation. In this test, the stack grows toward lower addresses.

```text
Higher SRAM addresses
0x00011000  chosen stack top before the test
            unused gap / boundary-test word area
0x00010f00  initial sp after reserving space below the boundary word
            function's 16-byte frame: saved ra at 12(sp)
            lower addresses are available for deeper calls
Lower SRAM addresses
```

At entry, `_start` sets `sp` to `0x10f00`. In `work`, `addi sp,sp,-16` reserves a 16-byte frame. `sw ra,12(sp)` saves the caller's return address. Then `jal ra,exercise_sram` writes a new return address into `ra`. When the nested function returns, `lw ra,12(sp)` restores the address that `work` must return to, and `addi sp,sp,16` releases the frame.

### What do `sp` and `ra` point to?

`ra` is register `x1`; `jal ra,target` writes the address of the next instruction into it and jumps to `target`. `jalr zero,0(ra)` jumps back to the address in `ra`. A second nested `jal ra,...` overwrites `ra`, so a function that still needs its earlier return address must save it first.

`sp` is register `x2`; it holds the current stack pointer, a byte address in RAM. It is not a function address and it does not automatically point to the beginning of a function. The software changes `sp` to reserve a frame, then uses offsets such as `12(sp)` to access words inside that reserved region. On entry to `work`, the caller's stack pointer is `0x10f00`; after subtracting 16, the current `sp` is `0x10ef0`. On return, adding 16 restores it to `0x10f00`.

In a compiled RISC-V program, arguments may be passed in registers, and only values that need storage are placed in the stack frame. A call does not automatically push every argument and return address. This hand-written example explicitly saves `ra` to make the overwrite-and-restore visible.

## Questions and answers

### Why use a stack if this test has only a small function?

The nested call makes the lifetime of the return address visible. `_start` calls `work`, and `work` calls `exercise_sram`. The second call writes a new value to `ra`; saving the first value in SRAM is what lets `work` return to `_start`. The same rule matters in recursion, interrupts, and any non-leaf function that makes another call.

### What does this test do to SRAM?

It writes `0x11223344` to the first word, replaces the low byte with `0xaa`, replaces the upper two bytes with `0xbbcc`, then expects `0xbbcc33aa`. It also writes and reads the final word at `0x00010ffc`. The firmware's function call uses a separate stack area.

### How is an undersized SRAM failure captured?

The runner repeats the program with only 256 bytes of SRAM. The test's chosen addresses and stack reservation no longer fit. The VexiiRiscv trap handler reads `mcause`, records it at the completion endpoint, and reports a store access fault (`mcause=7`). The runner requires that fault marker and rejects a normal completion marker. This ties the failure to an architectural exception instead of treating a simulator timeout as an explanation.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/04-sram/run.py
```

The nominal 4 KiB run must report the expected readback; the 256-byte run must report the expected store fault. Inspect `results/04/` and `results/04-small-ram/` for firmware images, maps, logs, and VCD traces. On this 32-bit word-addressed Wishbone interface, byte address `0x10000` is word address `0x4000`.

## What does a PASS prove?

The normal PASS checks the simulated SRAM's first/last locations, byte lanes, and stack use. The negative PASS checks that this firmware detects the deliberately insufficient capacity through a CPU store access fault. It does not prove timing or physical properties of a particular FPGA BRAM or ASIC macro; those require the implementation-specific memory and its own verification flow.
