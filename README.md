# SoC Integration Tour

This repository records a step-by-step attempt to understand how a small SoC is assembled and verified. The project uses LiteX and one VexiiRiscv core. Stages 00–06 are implemented and runnable; each stage keeps its hardware logic local and has its own README. The matching Chinese guides are named `README_zh.md`.

## Why build the system in small steps?

LiteX, HeteroSoC, or Chipyard can assemble a working SoC quickly. I also want to know what each piece contributes: which parameters select the CPU, who answers a bus request, how assembly turns into a ROM image, and how a software address reaches the intended hardware block. A full system can hide these boundaries behind generated RTL. This project exposes them in order, then uses LiteX to assemble the system again.

The rule for a stage is simple: change one integration question, run a positive case, and where useful create a controlled negative case. Keep the generated map, firmware, run log, and waveform as evidence. “Build succeeded” and “CPU ran the firmware” are different claims and get different checks.

## Stages 00–06

| Stage | Question being answered | Run |
| --- | --- | --- |
| 00 Environment | Which packages and tools generate the CPU RTL, firmware, and simulator? | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU bring-up | Can native VexiiRiscv leave reset, fetch a ROM word, and issue a known store? | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | What makes a request complete, and how do we catch missing or invalid ACK? | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | How do assembly, ELF, binary bytes, hex words, reset address, and ROM capacity fit together? | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | How does writable memory behave, and why does software need `sp` and save `ra` across a nested call? | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 Memory map | Which device responds to each address, and what happens in a hole or overlap? | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | What do `SoCCore`, `Builder`, and LiteX's native AXI-Lite-to-Wishbone adapter do? | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |

Run commands start at the repository root. Each chapter writes generated artifacts below `results/`; those files are ignored by Git so logs, waveforms, and build outputs stay local.

## One system, from source code to bus response

```text
program.S ── RISC-V GCC ──> ROM image ──> VexiiRiscv executes firmware
                                           │ AXI-Lite peripheral bus
                                           ▼
                               LiteX AXILite2Wishbone
                                           │ Wishbone main bus
                             ┌─────────────┼─────────────┐
                             ▼             ▼             ▼
                            ROM          SRAM       register endpoint
                                           │
                          LiteX Builder writes generated address maps
```

The diagram shows two related paths: Builder constructs and reports the hardware map; the CPU later sends real transactions through that hardware. The map check compares the generated report with the addresses used by firmware.

## Questions that guide the project

### Is Migen a LiteX module?

Migen is a separate Python hardware-description library. LiteX is built on Migen and uses it to describe and connect SoC hardware. The code may use Migen modules inside a LiteX design, but the two are separately installed packages and have distinct roles.

### Does LiteX natively support VexiiRiscv?

The pinned LiteX revision includes a native VexiiRiscv wrapper registered as `vexiiriscv`. This project selects its `standard` variant. The wrapper describes how the CPU integrates with LiteX; the VexiiRiscv Scala/SpinalHDL generator produces the CPU RTL, and `sbt` runs that generator.

### Is `AXILite2Wishbone` our code?

No. VexiiRiscv exposes an AXI-Lite peripheral bus, while this SoC uses LiteX's Wishbone main bus. LiteX's bus registration sees that the interfaces differ and inserts its native `AXILite2Wishbone` adapter. Stage 06 documents the code path and checks the generated build log for the adapter message. The project adds Wishbone endpoints but does not reimplement that bridge.

### Why are there byte addresses and word addresses?

Firmware and the generated memory map use byte addresses. A 32-bit Wishbone interface configured as word-addressed advances one address unit per four bytes. For example, byte address `0x40` appears as Wishbone word address `0x10`. Use the address unit printed next to a value before comparing firmware, maps, and bus traces.

### What does ACK mean?

`cyc` and `stb` mark an active Wishbone request. `ack` means the selected slave has completed that request. A value on `dat_r` without ACK is not a completed read. Stage 02 captures each cycle so a timeout, early ACK, held ACK, or wrong address has a concrete trace behind its PASS or failure.

### Why does the CPU need a stack?

`sp` is a software-maintained byte address in RAM that marks the current stack allocation. A `jal` writes the return address into register `ra`; a nested call overwrites that register. A function that still needs its earlier return address saves it in its stack frame and restores it before returning. The CPU does not automatically push all arguments and return addresses; the program and ABI decide what must be saved.

### Is the SRAM a physical macro?

Stages 04–06 use LiteX's Wishbone behavioral SRAM in simulation. It lets the test check bus-visible reads, writes, byte enables, and firmware use. An FPGA build must map the memory to a device block RAM or another implementation and verify the resulting latency and timing. An ASIC SRAM macro normally has native memory pins rather than Wishbone; a wrapper translates bus requests and returns ACK after the macro responds.

### What does the generated address map prove?

It proves which regions LiteX constructed and their origins/sizes. It does not prove that CPU instructions ran. Stage 06 checks the generated map before simulation, then requires a CPU completion write in the run log. Both pieces of evidence matter.

## Where to read next

Start with [Stage 00](chapters/00-environment/README.md), then continue in numerical order. Each chapter explains its question, circuit/data path, run command, expected evidence, and limits of what the PASS marker proves. [PLAN.md](PLAN.md) lists the next planned work; stages 07–15 are not yet implemented.
