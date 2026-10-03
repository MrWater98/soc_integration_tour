# 07 — Starting Bare-Metal C from ROM

This stage adds a 16 KiB main RAM and boots a freestanding C program without BIOS or an operating system. The CPU starts at reset address 0, executes `_start` from ROM, prepares writable sections and the stack, then enters `main()`.

```text
reset PC = 0
    │
    ▼
ROM: _start ── set sp ───────────────> RAM top
    │          ── copy .data LMA→VMA ─> main RAM
    │          ── zero .bss ─────────> main RAM
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

## What does this chapter add to the SoC configuration?

This chapter keeps the CPU, reset vector, ROM, and LiteX SRAM setup, then adds writable main RAM for C `.data`, `.bss`, and the stack. The settings remain in the `super().__init__(...)` call in `ProjectSoC`:

| Parameter | Stage 07 value | Why this stage needs it |
| --- | --- | --- |
| `integrated_main_ram_size` | `16 * 1024` bytes | Adds 16 KiB of main RAM at `0x40000000`; the linker puts `.data`, `.bss`, and the stack there. |
| `integrated_main_ram_init` | `[0xa5a5a5a5] * 4096` | Prefills every word of simulated 16 KiB RAM with a sentinel, so firmware detects a missing `.bss` clear. |
| `integrated_sram_size` | `0x1000` (4 KiB) | Keeps a separate SRAM at `0x10000000` in this map. The linker does not put C data or stack there; retaining it shows LiteX SRAM and main RAM as distinct regions. |

The reset address is still zero, and the ROM still starts there. The linker script declares `ENTRY(_start)` and uses `KEEP(*(.text.init))` to put `_start` first in ROM. `ENTRY` is ELF metadata; the VexiiRiscv reset vector is what makes the CPU fetch from address zero. The reset vector, ROM contents, and `_start` location must agree for the CPU to execute startup code after reset.

This chapter's `CompletionSlave` handles the test finish: the CPU writes `0x5a`, and the endpoint prints `SOC_COMPLETE` and ends simulation. It is not part of the C runtime and does not copy `.data` or clear `.bss`.

## How does `.data` get from ROM into RAM?

ROM does not push the contents into RAM, and LiteX does not perform a hidden copy when simulation starts. The linker assigns the source and destination addresses; the CPU executes ordinary load and store instructions in `_start` to copy each word.

In the linker script, `.data ... > main_ram AT > rom` gives `.data` two addresses: its runtime address (VMA) is in main RAM, while its initial bytes are stored in the ROM image at the load address (LMA). `__data_load_start` is the ROM source; `__data_start` and `__data_end` bound the RAM destination.

```text
At link time: initialized_data's initial value is placed in the ROM image

At runtime: the CPU executes _start
ROM 0x0000019c ── lw ──> CPU register t3 ── sw ──> RAM 0x40000000
                       0x11223344
```

In this build, the map gives `__data_load_start = 0x0000019c`, `__data_start = 0x40000000`, and `__data_end = 0x40000004`. The `.data` section is four bytes, so the loop runs once. Its key instructions are:

```asm
lw   t3, 0(t0)    # t0 points to the ROM load address; read one 32-bit word
sw   t3, 0(t1)    # t1 points to the RAM runtime address; write the word
addi t0, t0, 4    # advance source by four bytes
addi t1, t1, 4    # advance destination by four bytes
```

`la` loads a linker-provided symbol address into a register. The loop stops when the destination reaches `__data_end`. `lw` reads ROM and `sw` writes RAM as normal CPU load/store transactions; the SoC address decoder routes each access to the selected memory. `t3` temporarily holds the copied word in the CPU.

## Why clear `.bss`?

`.bss` holds static-storage variables that C requires to start at zero. Both `zero_initialized` and the uninitialized global array `scratch[4]` belong there. The linker marks `.bss` as `NOLOAD`, so it has no initial zero bytes in the ROM image to copy.

Startup therefore walks from `__bss_start` to `__bss_end` and stores zero into RAM. In this build, that half-open range is `[0x40000004, 0x40000018)`, covering `zero_initialized` and all four `scratch` elements.

The simulation pre-fills main RAM with `0xa5a5a5a5` so a missing clear becomes visible instead of accidentally passing. Without the startup loop, `zero_initialized` and `scratch[0]` would read as the sentinel value and fail the C check; only a successful check writes completion code `0x5a`. Real RAM power-up contents are not guaranteed to be zero either.

```text
RAM simulation prefill: A5 A5 A5 A5 A5 A5 ...
                              │ _start stores zero through .bss
                              ▼
main() observes:          00 00 00 00 00 00 ...
                          └─ zero_initialized and scratch[0] pass
```

## Questions and answers

### Why does reset need startup code before `main()`?

Reset makes the CPU fetch from the reset address; it does not perform the C runtime's memory work. `_start` copies each initialized `.data` word from its ROM load address to its RAM runtime address, writes zero through `.bss`, sets `sp`, and then calls `main`. Without those steps, initialized globals and zero-initialized globals would not have the values the C program expects.

### What are LMA and VMA in this program?

LMA is where the initial bytes are stored in the load image. VMA is where the program uses the section while running. `initialized_data` is stored after `.text` in ROM but its C address is in main RAM. The startup copy connects these two locations. Read `sections.txt` or `objdump -h` to compare them.

### Why does the check fail if `.bss` is not cleared?

By C rules, the global `zero_initialized` and `scratch` variables must start at zero, but they live in `.bss` and occupy no initialized ROM bytes. LiteX simulation pre-fills main RAM with `0xa5a5a5a5`, and startup must overwrite `.bss` word by word. Before changing `scratch[0]`, `main()` checks both `zero_initialized==0` and `scratch[0]==0`; without the clear, they read as `0xa5a5a5a5`, so firmware writes a failure code instead of `0x5a`. The prefill is a simulation sentinel. Real RAM may power up with other contents, but software must not assume it starts at zero.

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
