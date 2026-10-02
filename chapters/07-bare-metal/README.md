# 07 — Starting Bare-Metal C from ROM

This stage adds a 16 KiB main RAM and boots a freestanding C program without BIOS or an operating system. The CPU starts at reset address 0, executes `_start` from ROM, prepares writable sections and the stack, then enters `main()`.

```text
reset PC = 0
    │
    ▼
ROM: _start ── copy .data LMA→VMA ──> main RAM
    │          ── zero .bss ─────────> main RAM
    │          ── set sp ────────────> RAM top
    ▼
main(): check globals, scratch RAM, nested calls
    │
    └── write 0x5a to completion endpoint → simulation PASS
```

## What gets placed where?

| Region | Byte address | Contents |
| --- | --- | --- |
| ROM | `0x00000000`, 4 KiB | `_start`, `.text`, initial image for `.data` |
| LiteX SRAM | `0x10000000`, 4 KiB | On-chip working memory available in the SoC |
| main RAM | `0x40000000`, 16 KiB | `.data`, `.bss`, stack, scratch data |
| completion endpoint | `0x80000000`, 4 KiB | Simulation pass/fail probe |

The linker script defines the memory regions and output sections. The `.data` section has a load address (LMA) in ROM and a virtual/runtime address (VMA) in main RAM. `.bss` is `NOBITS`, so it has no initialized bytes in the ROM image and must be cleared by startup code.

## Questions and answers

### Why does reset need startup code before `main()`?

Reset makes the CPU fetch from the reset address; it does not perform the C runtime's memory work. `_start` copies each initialized `.data` word from its ROM load address to its RAM runtime address, writes zero through `.bss`, sets `sp`, and then calls `main`. Without those steps, initialized globals and zero-initialized globals would not have the values the C program expects.

### What are LMA and VMA in this program?

LMA is where the initial bytes are stored in the load image. VMA is where the program uses the section while running. `initialized_data` is stored after `.text` in ROM but its C address is in main RAM. The startup copy connects these two locations. Read `sections.txt` or `objdump -h` to compare them.

### How do we know `.bss` clearing really happened?

The simulation pre-fills all 4096 main-RAM words with `0xa5a5a5a5`. If startup forgets to clear `.bss`, the `zero_initialized` variable and scratch buffer will not accidentally read as zero. Firmware checks both initialized and zero values before it emits the completion code.

### Why does this test inspect `ra` and `sp` again?

`main()` calls `stack_roundtrip()`, which calls `use_stack()`. A non-leaf function must preserve its return address if another `jal` will overwrite `ra`. The runner checks the disassembly for `sw ra,...(sp)` and `lw ra,...(sp)`, then the CPU completion marker confirms the nested calls returned and the C checks passed. The linker also reserves room between heap candidate space and stack space.

### What does the 256-byte negative case prove?

The linker script contains an `ASSERT` that sections plus the minimum stack margin fit in RAM. The runner links the same program against 256 bytes and expects that assertion to fail. This proves a build-time capacity check works; it does not claim that the CPU ran with 256 bytes of RAM.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py
```

Expected output includes `EXPECTED_FAIL 07-SMALL-RAM`, followed by `SOC_COMPLETE ... data=0x0000005a` and `PASS 07`. Check `results/07/firmware/program.map`, `sections.txt`, and `disassembly.txt` against `linker.ld`; `builder/csr.csv` and `memory_map.csv` show the generated SoC map; `builder/gateware/sim_main_ram.init` proves the nonzero prefill; `small-ram/negative.log` records the rejected link; `run.log` and the VCD show runtime completion.

## What does a PASS prove?

The negative PASS proves that inadequate RAM is caught by the linker. The normal PASS proves that the real VexiiRiscv ran ROM startup, copied `.data`, cleared `.bss`, used main RAM and the stack, completed nested C calls, and reached the endpoint. ELF metadata alone proves none of that runtime behavior.
