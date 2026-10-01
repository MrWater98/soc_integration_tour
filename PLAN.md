# SoC Integration Project Plan

## Objective

Build a reproducible single-core RV32 SoC around LiteX and VexiiRiscv, first in simulation and then on a selected FPGA board. Keep the hardware contract, firmware, generated maps, and verification evidence together at each integration step. A stage is complete only when its build and runtime checks pass from a clean output directory.

The baseline CPU is LiteX's native `vexiiriscv` wrapper with the `standard` variant. Its peripheral port is AXI-Lite. The LiteX main bus is Wishbone Classic, so LiteX inserts its native AXI-Lite-to-Wishbone adapter when the CPU master is registered. The initial system is 32-bit, little-endian, single-clock, and single-core.

## Integration sequence

| Stage | Change to the system | Required evidence / exit gate |
| --- | --- | --- |
| 00 Host and source baseline | Pin LiteX, VexiiRiscv data and RTL source; install Python, Java/sbt, Verilator, C++ and RISC-V toolchain dependencies. | Strict environment report records versions, paths and missing dependencies. LiteX Wishbone baseline test passes. |
| 01 CPU reset path | Instantiate native VexiiRiscv, a small ROM and a memory-mapped write endpoint. | CPU fetches from reset address 0 and writes the expected value. A no-ACK run records a live request and times out without a false completion. |
| 02 Wishbone endpoint contract | Verify a 32-bit Wishbone master and register slave independently of the CPU. | Read/write, byte enables, configured waits, no response, early ACK, held ACK and unmapped address scenarios produce expected CSV/VCD and pass/fail markers. |
| 03 Firmware ROM | Assemble a small RV32 program, create a complete initialized ROM image and boot it. | ELF/bin/hex hashes are recorded; reset vector, image depth and generated map are checked; CPU reaches a completion write. |
| 04 Writable SRAM | Add Wishbone SRAM for data and stack; exercise full-word and partial-word writes plus nested calls. | First/last locations and byte lanes read back correctly. An undersized SRAM run reports the expected store access fault and no normal completion. |
| 05 Address decoding | Attach ROM, SRAM and a register endpoint to one shared main bus with explicit byte-address regions. | The map checker rejects overlap; firmware reaches each intended target; an unmapped load produces the expected access fault. |
| 06 LiteX SoC construction | Re-express the working design with LiteX `SoCCore` and `Builder`; retain a project completion endpoint. | Builder generates the expected memory and CSR maps; firmware is linked for those addresses; simulation reaches the completion endpoint. The generated log records AXI-Lite-to-Wishbone adaptation. |
| 07 Bare-metal C runtime | Add main RAM, startup code and a linker script; initialize `.data` and `.bss`, then enter C. | ELF, map and disassembly place code/data/stack in declared regions; firmware checks initialized and zeroed data and reports completion. |
| 08 GPIO | Add input/output GPIO CSRs and deterministic simulation pin stimulus. | Generated CSR addresses match firmware headers; output transitions and input samples match the test sequence. |
| 09 UART | Add UART with a fixed system clock and baud rate; verify transmit and receive paths. | Captured line-level bytes match the expected stream. Wrong-baud and reset-during-transmit cases are detected. |
| 10 Timer and interrupts | Add a timer and route one interrupt through the VexiiRiscv PLIC path. | Polling and ISR tests pass; source claim/complete and interrupt counts match; reset cases leave no stale interrupt. |
| 11 SPI and I2C | Add LiteX controllers and protocol-level slave models. | SPI mode/edge and I2C START/address/ACK/STOP transactions match expected bytes; wrong chip-select and NACK paths fail explicitly. |
| 12 External memory options | Integrate async SRAM, SDRAM through LiteDRAM, and memory-mapped SPI flash as separate configurations. | Each configuration completes a memory-specific initialization and readback check; capacity, map and initialization logs are saved. |
| 13 Integrated simulation regression | Combine the selected CPU, memory, GPIO, UART, timer and serial peripherals into one firmware-driven system. | One command runs the full regression with stable per-block markers, maps, tool versions and source hashes. |
| 14 FPGA target | Bind clocks, reset, pins and external devices to one named board target. | Board constraints are checked against the schematic and device documentation; synthesis and timing reports meet the declared clock target. |
| 15 FPGA runtime | Program the board and run the same software-visible self-checks. | Preserve the bitstream hash, board/tool versions and raw UART output; mark hardware-only tests SKIP when no board is present. |

## System contracts

### Processor and bus

- CPU: LiteX `vexiiriscv/standard`, RV32 little-endian, one hart.
- CPU peripheral interface: AXI-Lite, byte addresses.
- LiteX main bus: 32-bit Wishbone Classic, word-addressed endpoints where configured.
- Adapter: native LiteX `AXILite2Wishbone`; do not duplicate the protocol bridge in project logic.
- A transaction completes only on the target's valid response. Simulation endpoints must register ACKs and must not acknowledge an idle or stale request.

### Memory and firmware

- All software-visible maps and linker addresses are byte addresses.
- Record any bus-side word-address conversion next to the interface contract.
- ROM reset address must be aligned and inside the generated ROM region.
- Firmware images are derived from checked-in assembly/C and linker inputs; save image hashes and map files as generated evidence.
- Stack and heap reservations must fit inside RAM with explicit bounds. Negative capacity tests must fail before being reported as successful runtime tests.

### Build and verification

- Every stage has a root-relative command and writes outputs under `results/<stage>/`.
- Stage-local implementation files must not import another stage's implementation.
- Validate Builder output before starting CPU simulation.
- Require a unique success marker from firmware or a protocol checker; Python construction success is not a runtime pass.
- Bound all simulations and external commands with timeouts.
- Negative tests must check both the expected fault and absence of the normal completion marker.
- Generated build products and third-party checkouts remain outside version control; pin source revisions in the setup instructions.

## Repository layout

```text
chapters/
  00-environment/   host dependencies, source pins and environment verifier
  01-cpu-bringup/   reset, initial ROM fetch and first memory-mapped write
  02-wishbone/      bus endpoint protocol verification
  03-rom/           assembled firmware and initialized ROM
  04-sram/          data memory, byte lanes and stack accesses
  05-memory-map/    explicit regions, overlap and unmapped behavior
  06-litex-soc/     SoCCore/Builder realization of the working design
  07-15/            planned firmware, peripherals and FPGA integration
results/            ignored runtime evidence generated by each stage
```

## Current implementation status

The checked-in repository implements stages 00–06. Stages 07–15 are the next integration work and must not be described as implemented until their run commands and exit gates are present and verified.
