# SoC Integration Project Plan

## Objective and baseline

Build a reproducible single-core RV32 SoC around LiteX and VexRiscv, first in simulation and later on a selected FPGA. Keep each stage's hardware contract, firmware, maps, RTL inputs, and runtime evidence together.

The baseline is LiteX's native `vexriscv` CPU with the `minimal` variant: RV32I, no instruction cache, and no data cache. The CPU exposes separate instruction and data Wishbone masters. LiteX connects them to its shared Wishbone interconnect; there is no AXI-Lite-to-Wishbone bridge in this path. CPU RTL comes from the pinned `pythondata-cpu-vexriscv` package, so generating this CPU does not require Scala or SBT.

## Integration sequence

| Stage | Change | Required evidence |
| --- | --- | --- |
| 00 Environment | Pin LiteX, VexRiscv RTL data and host tools. | Strict environment report and Wishbone baseline test pass. |
| 01 CPU reset path | Add VexRiscv, a small ROM, and a memory-mapped write target. | Fetch from reset address 0 and expected write; missing ACK remains a live request and does not report completion. |
| 02 Wishbone endpoint | Verify read/write, byte enables, waits, missing/early/held ACK, and unmapped access. | Each case has an expected protocol result and recorded trace. |
| 03 Firmware ROM | Assemble RV32I firmware, create an initialized ROM image, and boot it. | Image depth, reset vector, memory map, and completion write agree. |
| 04 Writable SRAM | Add Wishbone SRAM for data and stack. | First/last locations and byte lanes read back; an undersized SRAM leaves the out-of-range Wishbone request unanswered, which the bounded test monitor captures. |
| 05 Address decoding | Attach ROM, SRAM, and a register endpoint to explicit address regions. | Overlap is rejected; mapped targets work; the unmapped request remains unacknowledged and is captured by the test monitor. |
| 06 LiteX SoC | Build the design with LiteX `SoCCore` and `Builder`. | Generated maps match firmware addresses and the CPU reaches the completion endpoint. |
| 07 Bare-metal C | Add main RAM, startup code, and linker sections. | `.data` copy, `.bss` clearing, stack, and C execution are verified. |
| 08 GPIO | Add input/output GPIO CSRs and deterministic pin stimulus. | CSR map, output transitions, and sampled inputs match expected values. |
| 09 UART | Add UART transmit/receive at a fixed clock and baud. | Captured bytes match; wrong-baud and reset cases fail explicitly. |
| 10 Timer and IRQ | Add a timer event routed to VexRiscv's external interrupt input. | Polling, ISR entry/return, pending-bit clear, and reset cases pass. LiteX IRQ source indices are checked against the generated map. |
| 11 SPI and I2C | Add LiteX controllers and protocol-level slave models. | SPI edges and I2C START/address/ACK/STOP match; wrong chip select and NACK are detected. |
| 12 External memory | Build separate async SRAM, LiteDRAM SDRAM, and SPI Flash configurations. | Each configuration passes its own initialization/readback check and saves its actual map and RTL. |
| 13 Integrated regression | Combine selected CPU, memory, GPIO, UART, timer, and serial peripherals. | One command runs firmware checks with stable markers, maps, tool versions, and source hashes. |
| 14 FPGA target | Bind clock, reset, pins, and memories to one named board. | Constraints match the board documentation; synthesis and timing meet the declared clock. |
| 15 FPGA runtime | Run the same software checks on hardware. | Preserve bitstream hash, tool versions, and raw UART output; mark unavailable board checks as not run. |

## Verification rules

- Compile RV32I firmware with the `minimal` variant's ISA and ABI (`-march=rv32i2p0 -mabi=ilp32`). Do not assume multiply/divide instructions exist.
- Keep byte addresses distinct from Wishbone word addresses in maps and traces.
- Give every wait loop a bound. A missing response must be reported as a protocol failure or timeout, never as a pass.
- Check the generated `csr.csv` and memory regions before running firmware that depends on them.
- A simulation pass proves the modeled behavior only. It does not prove FPGA timing, physical SRAM behavior, or board wiring.
- Preserve the complete RTL source list used to build each simulator under `results/<stage>/rtl/`.

## Repository layout

```text
chapters/
  00-environment/   host tools, pinned sources, and verifier
  01-cpu-bringup/   reset, ROM fetch, and first memory-mapped write
  02-wishbone/      protocol timing and failure models
  03-rom/           assembled firmware and ROM initialization
  04-sram/          data memory, byte lanes, and stack
  05-memory-map/    explicit regions and decode behavior
  06-litex-soc/     SoCCore and Builder
  07-bare-metal/    C startup, linker sections, and stack
  08-gpio/          CSR-backed input and output
  09-uart/          serial transmit and receive
  10-timer-irq/     timer event, external interrupt, and ISR
  11-spi-i2c/       serial peripheral protocols
  12-memory/        async SRAM, SDRAM, and SPI Flash experiments
results/            generated maps, logs, waveforms, and complete simulator RTL
```

Chapters 00–12 have runnable implementations. Chapters 13–15 remain planned integrated regression and FPGA work.
