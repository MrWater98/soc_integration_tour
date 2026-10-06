# SoC Integration Project Plan

[中文版](PLAN_zh.md)

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
| 13A JTAG/TAP basics | Build an independent TAP, IR/DR shifting, BYPASS, and an example IDCODE. | State traces, bit order, invalid instructions, short scans, and reset during scanning are checked. |
| 14 FPGA adaptation | Bind clocks, reset, pins, and memories to one named board. | Pin assignments, IO voltages, and clock constraints agree with board documentation. |
| 15 FPGA build | Synthesize, place, route, and generate a bitstream. | Resource budgets and target-clock timing are met; complete build reports are preserved. |
| 16 FPGA bring-up | Program the board and run startup and peripheral checks. | Board identity, programming logs, raw UART output, and per-test results are recorded. |
| 17 FPGA stability | Repeat cold starts and warm resets; stress memory, UART, and interrupts. | Defined duration and transaction counts are reached, errors are counted, and a reproducible version is frozen. |
| 17A SMP single-core comparison (optional) | Switch to `vexriscv_smp` with `cpu_count=1`. | Recheck ISA, caches, maps, and interrupt interfaces; rerun single-core checks. |
| 17B Dual-core SMP (optional) | Run two harts using shared-RAM mailboxes. | Each hart records its own count and completion code; repeated boot and shared-memory checks pass. |
| 18 ASIC specification | Select process, package, single-core features, memories, and test access. | Each requirement maps to RTL parameters, firmware tests, and constraints; library and macro sources are identified. |
| 19 ASIC RTL adaptation | Replace FPGA clock, memory, IO, and PHY resources. | Macro interfaces match bus responses, instances are bound, and boot/memory regressions pass. |
| 20 ASIC logic verification | Run lint, clock/reset-domain checks, coverage, and applicable formal verification. | Requirements trace to tests; boundary/fault cases pass; coverage gaps and waivers have a rationale. |
| 20A Scan and RAM test basics | Demonstrate internal-state access and fault detection using a small scan chain and RAM. | Shift/capture and March-style tests detect specified faults; normal operation resumes after test mode. |
| 21 DFT and technology synthesis | Implement process-specific scan/memory tests and mapped synthesis. | Chain connectivity, test coverage, area, and timing meet frozen targets; netlist functionality is checked. |
| 22 Constraints and floorplan | Define SDC, macros, IO/pad ring, and power distribution. | Critical paths are constrained, macro/power connections are correct, and floorplan/power budgets are feasible. |
| 23 Place, route, and STA | Place cells, build clock trees, route, extract parasitics, and analyze timing corners. | Setup/hold, slew, load, and congestion meet requirements; reports match the final netlist. |
| 24 Physical and electrical signoff | Check process-required DRC, LVS, antenna, density, ERC, IR/EM, and IO/ESD. | Process/project acceptance criteria are met; waivers are traceable and layout matches the netlist. |
| 25 Tapeout delivery | Freeze design/test deliverables, run project prechecks, and submit. | File lists, versions, hashes, and review records are complete; submission and acceptance have separate evidence. |
| 26 Post-silicon validation | Power up samples, check test access, boot, self-test, and characterize performance/power. | Per-device measurements link to the tapeout revision; faults and revision actions are recorded. |

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

## Execution plan through post-silicon

The main flow keeps single-core VexRiscv `minimal`. Stages 13–17 establish the FPGA system; stages 18–25 use single-core as the first ASIC baseline. Stages 17A–17B are an optional SMP branch. Stage 26 executes when silicon samples arrive.

Each stage records its inputs, implementation, acceptance conditions, and handoff outputs. Board, process, libraries, package, and memory capacity are selected at their respective stages. Clock frequency, test duration, coverage, and area budgets are frozen parameters.

### 13–13A: Integrated system and test access

**13 Integrated regression.** Combine the verified blocks into a declared ROM/RAM, GPIO, UART, timer, and SPI/I2C configuration. Run deterministic serial self-tests, then concurrent transactions, bus waits, and reset during accesses. Bound each test and check that interrupts preserve program state and stack. Deliver a common build entry, ELF/map, memory/IRQ maps, RTL source list, tool versions, and regression logs for FPGA and ASIC work.

**13A JTAG/TAP.** Use a separate small model to explain TCK/TMS/TDI/TDO, TAP states, IR instruction selection, DR scanning, BYPASS, and an example IDCODE. Record states and bit order; inject invalid instructions, short scans, and reset during scanning. Deliver waveforms and fault explanations. FPGA programming, boundary scan, and CPU debug depend on the hardware actually connected to the TAP. Select and verify compatible debug hardware separately when CPU debug is required.

### 14–17: FPGA implementation and hardware validation

**14 Board adaptation.** Start with the system baseline and a named board's schematic/device documentation. Use on-chip memory first; select board clock, reset polarity, UART/GPIO pins, IO voltage, and programming interface. Add external SDRAM/Flash according to the board configuration. Recalculate UART, SPI, I2C, and timer parameters. Deliver a board target, pin/clock constraints, configuration, and documentation traceability.

**15 Build.** Freeze tool versions and run synthesis, placement, routing, timing checks, and bitstream generation. Check bound CPU/interconnect/memory instances and inferred RAM type, capacity, latency, and byte writes. Accept against target clock, resource budget, and constrained critical paths. Preserve bitstream hash, resource/timing reports, and build commands.

**16 Bring-up.** Program the board through its actual interface. Check reset, UART startup markers, and RAM boundaries before GPIO, timer/IRQ, and protocol peripherals. Preserve board identity, bitstream/firmware revisions, programming logs, raw UART bytes, and failure waveforms. Hardware checks remain pending without a board.

**17 Stability.** Freeze duration, transaction counts, reset counts, and operating conditions. Repeat power-cycle boot and warm reset; stress memory patterns, UART, and interrupts. Check error counts, deadlock, and recovery. Deliver a stability report and a reproducible FPGA release whose software interfaces feed the ASIC specification.

### 17A–17B: Optional SMP branch

`vexriscv_smp` is a separate LiteX integration. Start with one hart and document ISA/ABI, cache, bus-width, reset-vector, CLINT/PLIC, and map differences. Recompile firmware and pin RTL sources/generation dependencies again.

For two harts, use separate shared-RAM mailboxes and let hart0 report combined results through UART. Define hart startup, shared-region cache policy, atomics, and memory barriers. Require independent execution evidence, repeated boot, and deadlock checks. FPGA deployment depends on the resource budget.

### 18–21: ASIC specification, adaptation, verification, and test

**18 Specification.** Select a process with available implementation data and a submission route. Freeze PDK, standard cells, IO library, package, single-core features, ROM/RAM capacities, clock, area/power budgets, and test access. Map each requirement to parameters, firmware checks, and constraints. Specify package pins for boot, reset, UART, and testing. Deliver a requirement/parameter/test/constraint matrix, library/macro inventory, pinout, and test specification.

**19 RTL adaptation.** Replace FPGA PLL, BRAM, IO, and PHY resources with ASIC implementations. Select fixed-logic ROM, an available ROM macro, or a loadable boot scheme and bind its firmware revision. Use RAM macros with functional models, Liberty, LEF, and layout views, or explicitly budget small register-based memories. Check ports, latency, write masks, read/write conflicts, power-up state, and supplies. Wishbone wrappers acknowledge when data is valid or writes complete; software initializes RAM. Deliver a technology top level, memory adapters, and passing boot/memory regressions.

**20 Logic verification.** Run lint, CDC/RDC, functional regression, coverage, and applicable formal properties on the ASIC top level. Cover boot, decode, bus waits, IRQ, memory, reset during transactions, and uninitialized reads. Use four-state simulation or randomized initial memory to expose initialization dependencies. Document coverage gaps, constraint exceptions, and waivers. Deliver a logic-freeze report tied to exact RTL/firmware revisions.

**20A Testability experiments.** Add scan enable/input/output to a few registers; demonstrate shift-in, functional capture, and shift-out comparison. Inject stuck-at and broken-chain faults and record detecting vectors. Apply March-style ascending/descending address sequences to a small RAM with data-bit and address faults. Deliver scan waveforms, a fault matrix, RAM traces, normal-mode recovery, and coverage numerators/denominators.

**21 Production DFT and synthesis.** Use the available libraries, macros, and tools to define scan chains, test clocks/reset, mode isolation, ATPG patterns, and memory testing. Specify the route from package pins to chains/macros. Check connectivity, fault coverage, and test time; rerun boot after test-mode exit. Map synthesis to frozen libraries, report logic/macro area, early timing, and power estimates, and perform applicable equivalence or gate-level checks. Deliver the mapped netlist, DFT configuration, vectors, and synthesis reports. Unavailable library/tool-dependent checks remain incomplete.

### 22–25: Physical implementation, signoff, and tapeout

**22 Constraints and floorplan.** Take the mapped netlist, library/macro views, pinout, and target clock. Write SDC for clocks, IO delays, uncertainty, and justified exceptions. Plan die/core size, utilization, macros, routing channels, pads, and power distribution. Check supplies, macro/IO connectivity, early congestion, and voltage drop. Deliver constraints, floorplan, power plan, and budget reports.

**23 Place and route.** Place cells, build clock trees, route, and extract parasitics. Run STA for the frozen process/voltage/temperature combinations; check setup/hold, clock skew, slew, and loads. Trace fixes to affected paths and rerun applicable equivalence/functional checks. Deliver final netlist, extraction data, and corner timing/area/power reports.

**24 Signoff.** Use the target process/project rules for DRC, LVS, antenna, density/fill, ERC, IR drop, electromigration, IO/ESD, and package constraints. Preserve tool/rule versions, results, remaining issues, and formal waiver rationale. Final GDS/OASIS, netlist, pinout, and reports must identify the same design revision. Deliver a per-item signoff checklist.

**25 Delivery.** Freeze source commit, CPU/SoC parameters, firmware/ROM, netlist, layout, constraints, library versions, scripts, test vectors, and signoff reports. Organize files against the actual MPW/foundry checklist and run prechecks; verify hashes and revisions. Record package readiness, formal submission, and acceptance separately with supporting evidence. Deliver the manifest and acceptance records, and prepare the test board, firmware, and measurement scripts.

### 26: Post-silicon validation and revision feedback

Inputs are traceable samples, package documentation, a test board, current-limited supplies, clocks, measurement equipment, and test vectors. Check package orientation, supply connections, and static current first. Validate clock, reset, and test access under the frozen plan; exercise scan/memory tests and boot after test-mode exit. Then run UART, RAM, GPIO, timer/IRQ, and peripheral self-tests.

For each device, record serial number, board identity, firmware hash, voltage, temperature, clock, vector revision, and results. Sweep frequency/voltage within permitted conditions and measure boot success, error rate, operating power, and highest stable frequency. Compare measurements with simulation, FPGA, and STA predictions. Preserve failure triggers, raw UART data, waveforms, reproduction steps, and revision actions.

Deliver per-device reports, functionality/performance/power measurements, issue records, and the next-revision plan. Without samples this stage remains planned. Freeze sample counts, test conditions, and acceptance criteria before execution.

## Handoffs and status

| Stage exit | Deliverables for the next stage |
| --- | --- |
| 13 | Integrated RTL, software interfaces, firmware, and automated regression baseline |
| 17 | Reproducible FPGA release, constraints, hardware self-tests, and stability report |
| 20 | Frozen ASIC RTL/firmware and requirement coverage report |
| 21 | Technology-mapped netlist, test access, vectors, and synthesis reports |
| 24 | Final layout, netlist, extraction data, and signoff checklist |
| 25 | Versioned/hashed package, submission, and acceptance records |
| 26 | Per-device measurements, reproducible issues, and revision plan |

Chapters 00–12 have runnable implementations. Stages 13–26, including 13A, 17A–17B, and 20A, are planned. Record PASS, FAIL, or SKIP/pending with evidence paths when checks execute; unavailable boards, process data, or samples retain their actual status.
