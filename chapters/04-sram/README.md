# 04 — Writable SRAM, Stack, and the Hardware Behind a Memory Model

Stage 03 had read-only firmware storage. This stage adds a 4 KiB Wishbone SRAM at byte address `0x00010000`. Firmware tests the first and last word, updates individual bytes, and calls a function that saves and restores its return address in SRAM.

## What kind of SRAM is this?

The design uses LiteX's `wishbone.SRAM`, a Migen-described behavioral memory with a Wishbone port. In this simulation, it is part of the generated SoC hardware. There is no separate SystemVerilog `tb.sv` that reimplements the SRAM. The CPU issues bus transactions; LiteX's SRAM module responds to them. This keeps the memory behavior and the interface being tested in the same design.

That model is enough to test address decoding, read/write behavior, byte enables, initialization assumptions, and firmware use of RAM. It does not model a particular chip's analog behavior, setup/hold limits, retention, power, or proprietary timing corners.

## How does LiteX place this SRAM in the SoC?

This chapter does not use `integrated_sram_size`. It explicitly creates `wishbone.SRAM(sram_size)` and attaches it to the Wishbone main bus with `bus.add_slave`. `SoCRegion(origin=0x10000, size=sram_size, mode="rw", cached=True)` declares its base, capacity, access mode, and cacheability hint. The selected VexRiscv `minimal` core has no cache, so this flag does not create a cache or hide SRAM transactions. The nominal 4 KiB setting matches the firmware's first and last addresses, `0x10000` and `0x10ffc`. The negative run changes the size to 256 bytes but keeps the firmware access at `0x10ffc`, outside the range. The stack remains inside the smaller RAM so the test reaches that intended access.

`mode="rw"` declares region permissions; it does not create a different SRAM circuit. The simulated response comes from `wishbone.SRAM`. `cached=True` is region metadata for the CPU/interconnect, appropriate for ordinary RAM. The completion register uses `cached=False` because each access can have an externally visible side effect. A real BRAM or SRAM macro also needs a wrapper whose latency, byte enables, and response timing match that memory's interface.

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

### Follow the stack through recursive `fact(3)`

For a concrete example, use a teaching convention where the argument and result use `a0`, and each call explicitly allocates an 8-byte frame. The frame stores `n` at its lower address and the saved `ra` four bytes above it. A compiler may choose a different frame layout under the ABI; this fixed one makes the register and memory changes easy to follow.

```c
int fact(int n) {
    if (n <= 1) return 1;
    return n * fact(n - 1);
}
```

Assume `sp=0x1000` before the call. The stack grows toward lower addresses. Each invocation executes `sp -= 8`, then stores its own `n` and `ra`:

```text
Higher addresses
0x1000  sp before the call (no fact frame yet)
        ┌──────────────────────────┐
0x0ffc  │ fact(3) saved ret_main   │  ← fact(3) sp = 0x0ff8
0x0ff8  │ fact(3) saved n = 3      │
        ├──────────────────────────┤
0x0ff4  │ fact(2) saved ret_fact3  │  ← fact(2) sp = 0x0ff0
0x0ff0  │ fact(2) saved n = 2      │
        ├──────────────────────────┤
0x0fec  │ fact(1) saved ret_fact2  │  ← fact(1) sp = 0x0fe8
0x0fe8  │ fact(1) saved n = 1      │  ← deepest current sp
        └──────────────────────────┘
Lower addresses
```

| Moment | Running function | Current `sp` | Meaning of `ra` now | Values retained on the stack |
| --- | --- | ---: | --- | --- |
| Before the call | Main | `0x1000` | No call to `fact` yet | No `fact` frame |
| Main calls `fact(3)` and allocates a frame | `fact(3)` | `0x0ff8` | `ret_main` | `n=3`, `ret_main` |
| `fact(3)` calls `fact(2)` and allocates a frame | `fact(2)` | `0x0ff0` | `ret_fact3` | Outer `n=3`, `ret_main`; current `n=2`, `ret_fact3` |
| `fact(2)` calls `fact(1)` and allocates a frame | `fact(1)` | `0x0fe8` | `ret_fact2` | Each level's own `n` and return address |
| `fact(1)` returns | `fact(2)` | `0x0ff0` | `ret_fact2`, used to resume `fact(2)` after its call | `a0=1`; frames for `fact(3)` and `fact(2)` remain |
| `fact(2)` computes `2×1`, restores its saved `ra`, and returns | `fact(3)` | `0x0ff8` | Restored as `ret_fact3` from the `fact(2)` frame | `a0=2`; only the `fact(3)` frame remains |
| `fact(3)` computes `3×2`, restores its saved `ra`, and returns | Main | `0x1000` | Restored as `ret_main` from the `fact(3)` frame, then used to return | `a0=6`; all `fact` frames are released |

The key point is that `sp` is not a function address. While `fact(2)` runs, `fact(3)`'s frame remains in RAM; the lower `sp` marks the newly reserved space for another frame. On return, the current call restores its saved `ra` and adds 8 back to `sp`, exposing the caller's frame again.

At the hardware level, `jal ra, fact` only writes the next instruction address into the general-purpose `ra` register and changes `pc` to `fact`. `addi sp,sp,-8` is ordinary register arithmetic. The `sw` instructions that save `n` and `ra` are ordinary CPU data-bus writes. The processor has no hidden “push stack frame” operation; software defines the convention and hardware executes the instructions.

## Questions and answers

### Why use a stack if this test has only a small function?

The nested call makes the lifetime of the return address visible. `_start` calls `work`, and `work` calls `exercise_sram`. The second call writes a new value to `ra`; saving the first value in SRAM is what lets `work` return to `_start`. The same rule matters in recursion, interrupts, and any non-leaf function that makes another call.

### What does this test do to SRAM?

It writes `0x11223344` to the first word, replaces the low byte with `0xaa`, replaces the upper two bytes with `0xbbcc`, then expects `0xbbcc33aa`. It also writes and reads the final word at `0x00010ffc`. The firmware's function call uses a separate stack area.

### How is an undersized SRAM failure captured?

The runner repeats the program with only 256 bytes of SRAM. The stack is kept inside that range; the final test store to byte address `0x10ffc` is outside it. The request stays active without ACK. This VexRiscv `minimal` RTL exposes Wishbone ERR as an input but does not turn the missing response into the architectural store-access trap this test originally expected, so the chapter records the bus-level wait instead of claiming an `mcause` result.

## Run and inspect
Each run snapshots the exact Verilog compiler inputs into [`results/04/rtl`](../../results/04/rtl) and [`results/04-small-ram/rtl`](../../results/04-small-ram/rtl). Each folder contains `sim.v`, the matching Vex CPU RTL, RAM support modules, and any ROM initialization files; `rtl_sources.txt` records the complete input list.

```sh
PYTHONHASHSEED=0 python3 chapters/04-sram/run.py
```

The nominal 4 KiB run must report the expected readback; the 256-byte run must report the expected out-of-range Wishbone request waiting without ACK. Inspect `results/04/` and `results/04-small-ram/` for firmware images, maps, logs, and VCD traces. On this 32-bit word-addressed Wishbone interface, byte address `0x10000` is word address `0x4000`.

## What does a PASS prove?

The normal PASS checks the simulated SRAM's first/last locations, byte lanes, and stack use. The negative PASS checks that the CPU requests the deliberately out-of-range address and the target does not acknowledge it. It does not prove timing or physical properties of a particular FPGA BRAM or ASIC macro; those require the implementation-specific memory and its own verification flow.
