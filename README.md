# Build and Verify a SoC from First Principles

This project assembles a small SoC around LiteX and one VexiiRiscv core. Each stage isolates one part of the integration and demonstrates it with a runnable experiment, from CPU fetch and bus responses to ROM images, RAM, address decoding, and LiteX SoC generation.

## Build in small steps

LiteX, HeteroSoC, or Chipyard can assemble a working system quickly. I also want to understand the smallest useful construction and test for each piece: which parameters select the CPU, who completes a bus request, how assembly becomes a ROM image, and how a software address reaches its hardware target. Splitting the boundaries makes it easier to tell whether a failure comes from the CPU, firmware, bus, or map.

Each experiment keeps evidence such as generated maps, compiler outputs, cycle logs, and waveforms. A successful build only shows that the hardware description was generated. A completion write from the CPU or a protocol checker reading back the expected value is runtime evidence. Negative cases also have an explicit expected result, such as a bounded timeout when ACK is missing or an access fault for an unmapped address.

## Stages and run commands

Run commands from the repository root. Generated files go under the Git-ignored `results/` directory.

| Stage | Focus | Run |
| --- | --- | --- |
| 00 Environment | CPU, firmware, and simulator toolchain | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU bring-up | Reset, instruction fetch, and a known store | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | Request/response timing and failure cases | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | Assembly-to-ROM image and reset mapping | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | Byte lanes, stack frames, and returns | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 Memory map | Address regions, overlap, and unmapped access | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`, `Builder`, and AXI-Lite/Wishbone integration | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 Bare-metal C | Startup, `.data`, and `.bss` initialization | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | GPIO input/output through CSRs | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | UART FIFO and 8N1 pin waveform | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 Timer and IRQ | Timer events, PLIC, and ISR return | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI and I2C | Bit-banged serial protocols and NACK handling | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 External memory | Parallel SRAM, SDRAM, and SPI Flash access paths | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

Stages 00–12 have chapter guides and run entries. Stage 12 additionally requires the pinned LiteDRAM checkout described in its README. Stages 13–15 remain planned integrated regression and FPGA work.

## From source to a bus response

```text
VexiiRiscv Scala/SpinalHDL ── sbt ───────> CPU Verilog
RISC-V C / assembly ──────── GCC/objcopy ─> ELF / ROM image
LiteX SoCCore + Migen modules ─ Builder ──> SoC gateware / address maps
CPU AXI-Lite peripheral port ─ AXILite2Wishbone ─> Wishbone main bus
                                                     ├── ROM
                                                     ├── SRAM / external memory controller
                                                     └── CSRs / project endpoint
Verilator + C++ ────────────────────────────────> cycle-level simulation
```

These are separate build steps: `sbt` generates CPU RTL, RISC-V GCC builds software, LiteX/Migen assembles the SoC, and Verilator compiles the simulator. Their outputs serve different purposes.

## Reading the chapters

Each chapter README can be read on its own and includes the experiment, a connection or signal diagram, run command, log/waveform locations, and what its PASS can establish. Start with [Stage 00](chapters/00-environment/README.md); the full sequence is in [PLAN.md](PLAN.md).
