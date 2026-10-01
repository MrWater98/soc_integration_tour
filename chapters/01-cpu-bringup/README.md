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
