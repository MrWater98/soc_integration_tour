# SoC Integration Tour

This project builds a small single-core RV32 SoC around LiteX and **VexRiscv**. The default teaching CPU is LiteX's `vexriscv/minimal` variant: RV32I, with no instruction or data cache. The CPU exposes instruction and data Wishbone buses directly; LiteX connects those masters to the SoC's Wishbone interconnect.

Each chapter isolates one integration step and records evidence under `results/<stage>/`: generated address maps, firmware images, simulator logs, waveforms, and the RTL files passed to the simulator compiler. A generated design is not runtime proof; a CPU completion write or a protocol checker reading back the expected value is.

## Current progress (2026-10-22)

The project now covers **real Tang Primer 20K Dock operation and ICS55 ASIC core adaptation and verification**, with chapters through 20 and an additional 20A DFT lab.

- **00–13:** CPU, buses, memories and peripherals, followed by integrated self-tests and failure regression.
- **13A–13F:** JTAG, boundary scan, OpenOCD, GDB, simulator comparison and neural operator acceleration. The GDB lab currently debugs a native program; it does not yet control the SoC CPU over JTAG.
- **14–17:** Open FPGA builds and board operation, including recorded 54 MHz runs for 600 seconds, ten warm resets and a 27 MHz run for 120 seconds. The 17A/B SMP designs have RTL simulation evidence; FPGA operation remains pending.
- **18–20A:** An ICS55 process pilot, cache-free RV32I core mapping and functional simulation, fault/coverage checks, internal scan and RAM March labs. SRAM macros, production DFT, physical implementation and tapeout signoff remain on the roadmap.

Start with the [progress and result guide](docs/progress/README.md), then the [current plan](PLAN.md). The [import validation record](docs/progress/VALIDATION.md) separates historical evidence from checks replayed locally in this repository. Existing chapters 00–12 were not individually rerun during this import. The current plan and most added teaching material are in Chinese; [README_zh.md](README_zh.md) provides the Chinese homepage.

## Chapters

Run commands from this repository root. Generated artifacts are written to `results/`.

| Chapter | Experiment | Command |
| --- | --- | --- |
| 00 Environment | Python, LiteX, VexRiscv RTL, Verilator, and toolchain checks | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU bring-up | Reset, instruction fetch, first Wishbone write, and missing ACK | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | Response timing and failure cases | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | Assemble a program and boot its ROM image | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | Byte lanes, stack storage, and out-of-range access | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 Memory map | Regions, overlap, and unmapped access | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`, `Builder`, maps, and Wishbone devices | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 Bare-metal C | Startup code, `.data`, `.bss`, and stack | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | CSR controlled inputs and outputs | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | UART FIFO and 8N1 pin waveform | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 Timer and IRQ | Timer polling, machine external interrupt, and ISR return | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI / I2C | Controller transactions and NACK handling | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 External memory | Async SRAM, SDRAM, and SPI Flash configurations | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

The CPU RTL is supplied by the pinned `pythondata-cpu-vexriscv` package; no Scala or SBT CPU-generation step is part of this flow. GCC builds firmware, LiteX/Migen builds the SoC, and Verilator builds the cycle simulator.

## Hardware path

```text
VexRiscv instruction Wishbone ─┐
                               ├─ LiteX shared Wishbone ─ ROM / SRAM / CSR / devices
VexRiscv data Wishbone ────────┘

RISC-V assembly/C ─ GCC + objcopy ─ firmware image
LiteX + Migen ─ Builder ─ generated RTL and address maps
Verilator + C++ ─ cycle simulation
```

## Added chapters and reading guide

| Chapter | Topic | What you learn |
| --- | --- | --- |
| 13 | [Integrated SoC and failure regression](chapters/13-integration/README.md) | Firmware self-test, concurrent peripherals, wrong CSR/IRQ and corrupt ROM |
| 13A | [JTAG / TAP](chapters/13a-jtag-tap/README.md) | Pin-level capture, shift, update and TAP state transitions |
| 13B | [Boundary scan](chapters/13b-boundary-scan/README.md) | Input sampling, output control and connection faults |
| 13C | [OpenOCD](chapters/13c-openocd/README.md) | Real OpenOCD controlling a simulated TAP through remote_bitbang |
| 13D | [GDB](chapters/13d-gdb/README.md) | Breakpoints, stack and registers in a native recursive program |
| 13E | [Simulator comparison](chapters/13e-tool-comparison/README.md) | Tool capabilities, scope and execution records |
| 13F | [Neural operator acceleration (optional)](chapters/13f-cfu-ml/README.md) | Upstream CFU, INT8 dot products, real custom instructions and software comparison |
| 14 | [Tang FPGA platform](chapters/14-fpga-platform/README.md) | Clock, pins, CSR, C firmware and generated-file walkthroughs |
| 14E | [Place-and-route experiments](chapters/14e-seed-sweep/README.md) | Seeds, RAM sizes, placement algorithms and timing weights |
| 15 | [Open FPGA build](chapters/15-fpga-build/README.md) | Yosys → nextpnr → Apicula → .fs |
| 16 | [Board bring-up](chapters/16-board-smoke/README.md) | WSL USB, JTAG loading, LEDs, UART and reset |
| 17 | [Board stability](chapters/17-fpga-stability/README.md) | RAM transaction counts, IRQ, UART, continuous runs and warm resets |
| 17A | [Single-hart SMP](chapters/17a-smp-single/README.md) | Real SMP RTL with per-hart stack, atomics and CLINT |
| 17B | [Dual-hart SMP](chapters/17b-smp-dual/README.md) | Shared RAM, mailboxes, atomic counters and failure cases |
| 18 | [ICS55 PDK and mapping pilot](chapters/18-ics55-spec/README.md) | Pinned PDK, standard-cell mapping, gate simulation and single-corner STA |
| 19 | [ASIC RTL adaptation](chapters/19-asic-rtl/README.md) | Small RV32I SoC, memory inventory, constant ROM and flip-flop RAM |
| 20 | [ASIC verification package](chapters/20-asic-verification/README.md) | Faults, resets, random transactions, bounded properties, lint and line coverage |
| 20A | [DFT basics](chapters/20a-dft-basics/README.md) | Internal scan, RAM March and enumerated fault detection |

## Source to results

```text
C + startup assembly + linker script ─ GCC ─ firmware / map / disassembly
LiteX Python + RTL ─ Migen / Builder ─ SoC RTL / ROM initialization / CSR headers
                                              │
                              ┌───────────────┴──────────────┐
                              ▼                              ▼
                      simulation and faults         synthesis / FPGA routing
                              │                              │
                     logs / CSV / coverage          netlists / timing / .fs
```

Sources and explanations live in `chapters/`. Complete RTL input snapshots, including initialization files, live in `results/<experiment>/rtl/`. Start with `summary.json` or `REPORT.md`, then inspect logs and firmware disassembly. See the [generated-file guide](docs/generated-files/README.md) for Builder outputs. Large waveforms and compiler intermediates are rebuilt locally.

Configurations vary by experiment: the 00–12 baseline uses `minimal`, the CFU lab uses `full+cfu`, SMP uses a separate configuration, and chapter 19 returns to a small cache-free RV32I core. The shared Wishbone diagram above represents the baseline; chapter 19 uses a crossbar. GPIO width, memory size, clocks and timeout counts are configuration choices.

## Check and replay

Run from this repository root; install dependencies using the relevant chapter instructions.

```sh
# Verify imported hashes, Python syntax, initialization files and tool locations.
python3 tools/check_progress.py

# Replay six selected 19/20 checks from supplied snapshots; requires Icarus Verilog.
python3 tools/verify_import.py

# Run standalone scan and RAM March experiments; requires Icarus Verilog.
python3 chapters/20a-dft-basics/run.py --output results/20a-local
```

Local replay passed chapter 19 RTL, generic and ICS55-mapped startup, plus chapter 20 repeated startup and detection of missing ACK and incorrect GPIO. Standalone CFU and DFT labs also passed locally. Full chapter 20 regression, fresh process mapping and board loading have separate chapter commands.
