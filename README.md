# Build and Verify a SoC from First Principles

This project assembles a small SoC around LiteX and one VexiiRiscv core. Each stage asks one integration question and answers it with a runnable experiment: can the CPU fetch, who responds to a bus request, how does firmware become ROM contents, how do RAM and address decoding fit, and what does LiteX generate for a complete SoC?

## Why build it in small steps?

LiteX, HeteroSoC, or Chipyard can assemble a working system quickly. I also want to understand the smallest useful construction and test for each piece: which parameters select the CPU, who completes a bus request, how assembly becomes a ROM image, and how a software address reaches its hardware target. Splitting the boundaries makes it easier to tell whether a failure comes from the CPU, firmware, bus, or map.

Each experiment keeps evidence such as generated maps, compiler outputs, cycle logs, and waveforms. A successful build only shows that the hardware description was generated. A completion write from the CPU or a protocol checker reading back the expected value is runtime evidence. Negative cases also have an explicit expected result, such as a bounded timeout when ACK is missing or an access fault for an unmapped address.

## Stages and run commands

Run commands from the repository root. Generated files go under the Git-ignored `results/` directory.

| Stage | Question | Run |
| --- | --- | --- |
| 00 Environment | Which tools produce the CPU, firmware, and simulator? | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU bring-up | Can VexiiRiscv leave reset, fetch, and issue a known store? | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | How does a request complete, and how are missing, early, or held ACKs caught? | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | How do assembly, ELF, bytes, 32-bit words, reset address, and ROM depth relate? | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | How does writable RAM support byte lanes, stack frames, and returns? | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 Memory map | Which device answers an address, and what happens on overlap or a hole? | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | What do `SoCCore`, `Builder`, and the AXI-Lite/Wishbone adapter do? | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 Bare-metal C | How does startup initialize `.data` and `.bss` before entering C? | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | How does the CPU control outputs and read inputs through CSRs? | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | How does a CSR write become an 8N1 waveform on the serial pin? | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 Timer and IRQ | How does a peripheral event enter an ISR through the PLIC and return? | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI and I2C | Can the controllers follow protocol timing and detect NACK? | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 External memory | How do parallel SRAM, SDRAM, and SPI Flash differ? | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

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

## Questions and answers

### Is Migen part of LiteX?

Migen is a separate Python hardware-description library. LiteX builds on Migen, using its signals, modules, and synchronous logic to provide SoC components such as CPUs, buses, memories, CSRs, and Builder. They are separate software packages.

### Does LiteX natively support VexiiRiscv?

The pinned LiteX revision has a native VexiiRiscv wrapper registered as `vexiiriscv`; this project selects the `standard` variant. LiteX's wrapper connects the CPU to the SoC. VexiiRiscv's Scala/SpinalHDL generator produces the CPU RTL, run by `sbt`. `pythondata-cpu-vexiiriscv` supplies CPU data and generator sources needed by the wrapper.

### Is `AXILite2Wishbone` project code? Why is it absent from our Python files?

It is a built-in LiteX bridge. VexiiRiscv exposes an AXI-Lite peripheral bus, while this system uses Wishbone as the main bus. When LiteX registers the CPU master, it detects the protocol mismatch and inserts `AXILite2Wishbone`. The project selects the CPU, builds the SoC, and adds slaves; it does not need to instantiate the bridge itself. Stage 06's `build.log` records the adaptation.

### Why can an address differ by a factor of four?

Firmware and LiteX memory maps use byte addresses. A 32-bit Wishbone interface configured for word addressing advances one address unit per four bytes, so software address `0x40` can appear as bus address `0x10`. The data remains `0x40`; only the address unit changes. Four `sel` byte-enable bits select which bytes of the 32-bit word are active.

### What does Wishbone ACK mean, and how do we locate a failure?

`cyc/stb` mark a valid request; `ack` means the slave completed that access. Read data without ACK is not a completed read. Stage 02 samples the address, request, ACK, and data each cycle into CSV/VCD. A missing ACK times out within a bound; an early ACK is caught before a request; a held ACK is caught after the master withdraws the request; an unmapped address appears in the trace as outside the slave's range. The checker decides pass/fail while the waveform preserves the evidence.

### How does assembly become ROM contents, and what does `memory_map` do?

RISC-V GCC links assembly into an ELF. `objcopy` extracts flat binary bytes. A project script groups each four little-endian bytes into one 32-bit ROM word and pads the image to its configured depth. The CPU fetches those words from its reset address. A memory map records which hardware region owns each byte address, while checks validate origins, sizes, alignment, and overlap. The bus regions implement the decode; a table alone does not create hardware.

### What are `sp` and `ra`?

`sp` is general-purpose register `x2`, holding a RAM byte address at the current stack-frame boundary. It is not a function address. Software changes it to reserve frame space, then uses offsets to access locals and saved values. `ra` is register `x1`; `jal` writes the next instruction address there and jumps. A nested call overwrites `ra`, so a function that still needs its earlier return address saves it in its frame and restores it before returning. The hardware executes `addi`, `sw`, `lw`, `jal`, and `jalr`; stack frames are a software convention. Stage 04 traces `sp`, `ra`, and memory through recursive `fact(3)`.

### Is this a physical SRAM? Why does an external test need a model?

LiteX's `wishbone.SRAM` is an internal behavioral memory, suitable for testing bus wiring, reads, writes, byte enables, and software access. Stage 04 tests that LiteX memory directly, so a second copy in `tb.sv` would not add a memory implementation to the SoC. Stage 12's asynchronous SRAM sits beyond a LiteX bus bridge: LiteX drives the chip pins, while a Verilog model on the other side stores bytes and responds to reads and writes. These models sit at different interface boundaries.

FPGA synthesis usually maps inferred memory to on-chip block RAM. ASIC designs often use a hard SRAM macro. A physical SRAM macro normally has no Wishbone port; a wrapper translates Wishbone requests to its address, enable, and write-mask pins, then returns ACK after the macro's latency. Functional simulation checks the data path; device mapping, timing, and physical properties require their corresponding implementation flows.

### Does a generated LiteX map prove the CPU ran?

No. `csr.csv` and `csr.json` prove which regions and register addresses LiteX constructed, but not that the CPU fetched instructions or completed a transaction. Stage 06 compares the generated map with firmware's addresses, then runs the CPU and requires the endpoint's expected completion write. The map and runtime marker answer different questions: “Was it built as intended?” and “Did the program run through it?”

### What are the Python helpers in Stage 06?

`tour_paths.add_litex_to_path` locates LiteX source and sets the import path; it does not install dependencies. `build_program` invokes RISC-V GCC and `objcopy`. `write_rom_init` checks capacity and pads the image. `ProjectSoC` describes the LiteX system. `build_and_run` runs Builder, map checks, simulator compilation, and log validation. `check_generated_map` compares Builder output with firmware's address contract. Except for LiteX's `Builder`, these are project scripts, not LiteX APIs.

## Reading the chapters

Each chapter README can be read on its own and includes the experiment, a connection or signal diagram, run command, log/waveform locations, and what its PASS can establish. Start with [Stage 00](chapters/00-environment/README.md); the full sequence is in [PLAN.md](PLAN.md).
