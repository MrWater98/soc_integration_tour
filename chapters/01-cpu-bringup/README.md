# 01 — Can VexiiRiscv Fetch and Store?

This is the first CPU-level experiment. It uses LiteX's native VexiiRiscv wrapper, a 64-byte initialized ROM, and a small memory-mapped write endpoint. The test is deliberately short so the log has only a few events to interpret.

```asm
addi x1, x0, 64   # x1 = 0x40
sw   x1, 0(x1)    # store 0x40 at byte address 0x40
```

## What is connected?

```text
VexiiRiscv pBus (AXI-Lite, byte address)
                 │
                 ▼  LiteX AXILite2Wishbone adapter
         Wishbone Classic, 32-bit
          ├── ROM       0x00000000–0x0000003f
          └── endpoint  0x00000040–0x0000007f
```

The CPU's peripheral bus is AXI-Lite. The LiteX main bus in this setup is Wishbone. LiteX inserts the protocol adapter when it registers the CPU bus master; this project does not implement the adapter.

## First use of `SoCCore`: what do these parameters configure?

This chapter's `ProjectSoC` inherits from LiteX `SoCCore`. Calling `super().__init__(...)` asks LiteX to build the CPU, main bus, and integrated memories from the supplied parameters. The chapter then adds its own `WriteTarget` as the CPU store destination; `SoCCore` does not create this experiment-specific endpoint.

| Parameter | Value here | Why it is set this way |
| --- | --- | --- |
| `platform` | Simulation `SimPlatform` | Describes the simulated clock/pins, not a physical board. The runner adds a `CRG` for the `sys` clock domain. |
| `clk_freq` | `1_000_000` | Declares the system clock frequency for LiteX and simulation configuration. This two-instruction test does not depend on peripheral baud timing. |
| `cpu_type` | `"vexiiriscv"` | Selects LiteX's natively registered VexiiRiscv wrapper. |
| `cpu_variant` | `"standard"` | Selects the VexiiRiscv configuration used by this project. |
| `cpu_reset_address` | `0` | Sets the CPU reset vector. LiteX passes it to the VexiiRiscv generator, and the generated RTL resets PC to zero. |
| `integrated_rom_size` | `0x40` (64 bytes) | Allocates only enough ROM for this short instruction sequence. SoCCore maps the ROM at the CPU reset address, zero. |
| `integrated_rom_init` | 16 machine-code words | Loads the `addi`, `sw`, stop loop, and NOP fill into ROM; it does not set the CPU reset location. |
| `integrated_sram_size` | `0` | No SRAM region is needed for this first CPU experiment. |
| `integrated_main_ram_size` | `0` | The program has no C runtime, stack, or writable data section, so it does not need main RAM yet. |
| `with_uart / with_timer / with_ctrl` | All `False` | Disables default UART, Timer, and control modules unused here, keeping the observed path small. |

`bus_standard` is not passed, so LiteX uses its default Wishbone main bus. VexiiRiscv exposes an AXI-Lite peripheral port; LiteX detects the protocol difference when registering the CPU master and inserts `AXILite2Wishbone`. This is why the code uses `SoCCore` but never calls the bridge directly.

### How does this chapter attach a custom block to LiteX?

`SoCCore` creates the common SoC structure; the project must register its own endpoint. `add_module("write_target", ...)` adds the Migen module to the design hierarchy, `bus.add_slave(...)` connects its Wishbone interface to LiteX's main bus, and `SoCRegion(origin=0x40, size=0x40, ...)` tells the decoder which addresses it answers. `SoCIORegion` also registers this low range as a CPU-visible I/O region. Creating a module without `add_slave` would leave CPU bus accesses disconnected from it.

Read these settings as a group: the CPU reset vector is `0`, the integrated ROM also starts at `0`, and its initialized words must contain code for that location. The endpoint starts at `0x40`, immediately after the ROM range `0x00–0x3f`, so the regions do not overlap. `integrated_rom_size` is measured in bytes, while each item in `integrated_rom_init` is one 32-bit word; 16 words are exactly 64 bytes here. If the ROM is enlarged without moving the endpoint, the ROM claims address `0x40`; if only the reset address changes, the CPU fetches from a location that the current image was not linked for.

### Why does PC return to zero on reset?

`cpu_reset_address=0` is a build-time setting; Python does not write PC on every clock. LiteX calls the CPU wrapper's `set_reset_address(0)` and passes `--reset-vector 0` while generating VexiiRiscv RTL. The CPU reset signal makes RTL reset PC to zero; after reset is released, the CPU fetches from address zero. SoCCore also maps the integrated ROM at the reset address, so ROM contents are available at zero.

```text
SoCCore: cpu_reset_address=0
       ├── VexiiRiscv RTL: reset PC ← 0
       └── integrated ROM: origin = 0
                                  │
CPU fetches from 0 after reset ───┘
```

The reset vector must match the ROM contents: firmware must be stored where the CPU begins fetching. This first experiment has no ELF `ENTRY` or linker script; the ROM is initialized directly through `integrated_rom_init`.

## Questions and answers

### Why start with only two instructions?

`addi` creates a known value, and `sw` turns it into an observable bus transaction. If the endpoint sees the expected address and data, the CPU left reset, fetched instructions, decoded and executed them, and issued a store. There is no C runtime, stack setup, or unrelated peripheral to obscure the first result.

### Does the first `FETCH` prove the instruction executed?

It proves that a read request at the ROM reset address completed. VexiiRiscv can prefetch, so a fetch log alone does not prove that a particular instruction retired. The endpoint's `0x40` write is stronger evidence: it can only happen after the program reaches the `sw`.

### Why does `0x40` become Wishbone address `0x10`?

The firmware and LiteX memory map use byte addresses. This 32-bit Wishbone endpoint is configured with word addressing, so one bus address step represents four bytes. Thus byte address `0x40` corresponds to Wishbone word address `0x40 / 4 = 0x10`. The stored value stays `0x40`; the conversion changes the address unit, not the data.

### Where is `AXILite2Wishbone` in the Python files?

The chapter selects VexiiRiscv and LiteX's Wishbone main bus. During CPU master registration LiteX checks the two bus types and adds its built-in `AXILite2Wishbone` adapter. The design log reports `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit`. The class lives in LiteX's `litex/soc/interconnect/axi/axi_lite_to_wishbone.py`; no project Python file needs to call it directly.

### What exactly does the no-ACK case show?

The endpoint is configured not to acknowledge the store. The CPU's request stays pending: the log records `DATA_WAIT` with byte address `0x40` and value `0x40`, then the bounded simulation times out. The test passes because it detects a live request that did not complete. It must not print the normal write-completion marker. This distinguishes “CPU issued a request” from “the target accepted the transaction.”

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

The first command runs the real CPU once with a responding endpoint and once with ACK suppressed. The second command is a small timing exercise for a toy bus endpoint; it is useful for understanding the handshake, but it is not a substitute for CPU simulation.

Look under `results/01/` and `results/01-no-ack/` for build logs, run logs, generated maps, and VCD traces. In a waveform, follow reset, the CPU AXI-Lite request, Wishbone `cyc/stb`, and the endpoint `ack`. A request is active while `cyc` and `stb` are high. It completes only when the selected target responds.

## What does a PASS prove?

The normal PASS proves that VexiiRiscv fetched from reset and caused the endpoint to observe the expected store. `PASS 01-NO-ACK` proves that the test caught a request that never received ACK; it does not mean the store succeeded. Stage 02 isolates the slave response rules so each fault is easier to identify.
