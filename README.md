# SoC Integration Tour

This project builds a small single-core RV32 SoC around LiteX and **VexRiscv**. The default teaching CPU is LiteX's `vexriscv/minimal` variant: RV32I, with no instruction or data cache. The CPU exposes instruction and data Wishbone buses directly; LiteX connects those masters to the SoC's Wishbone interconnect.

Each chapter isolates one integration step and records evidence under `results/<stage>/`: generated address maps, firmware images, simulator logs, waveforms, and the RTL files passed to the simulator compiler. A generated design is not runtime proof; a CPU completion write or a protocol checker reading back the expected value is.

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

Chapters 00–12 contain runnable experiments. Chapters 13–15 remain planned integrated regression and FPGA work. See [PLAN.md](PLAN.md) for the stage contracts and [the Chinese guide](README_zh.md) for the student-oriented walkthrough.
