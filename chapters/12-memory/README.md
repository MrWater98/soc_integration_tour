# 12 — Three External Memories, Three Access Paths

This stage builds three separate SoCs around the same VexiiRiscv core. The CPU always boots from on-chip ROM. It then accesses one selected external memory: asynchronous SRAM over parallel pins, SDRAM through LiteDRAM, or SPI Flash through a serial read bridge. These are independent configurations; their maps must not be combined.

| Memory | CPU-visible region | What the stage checks |
| --- | --- | --- |
| Asynchronous SRAM | `0x90000000–0x90000fff`, 4 KiB | 32-bit Wishbone requests become byte-wide pin operations; waits, masks, boundaries, readback |
| SDR SDRAM | `0x40000000–0x403fffff`, 4 MiB | initialization, data patterns, boundaries, automatic refresh and post-refresh readback |
| SPI Flash | `0xa0000000–0xa0000fff`, read-only 4 KiB window | command `0x03`, 24-bit address, 32 data clocks, header/checksum/boundary |

The SRAM and Flash tests use separate uncached IO regions so each bus read is visible as an external transaction. The SDRAM test maps DRAM as `main_ram` and uses the on-chip SRAM for its stack and C runtime during initialization. It checks data access; it does not execute code from SDRAM.

## Why do the three `SoCCore` configurations differ?

All three builds keep the same VexiiRiscv, reset address `0`, and 4 KiB boot ROM. Their writable memories differ to match the job each firmware performs:

| Build | `integrated_sram_size` | `integrated_main_ram_size` | External LiteX block and sensitive settings |
| --- | ---: | ---: | --- |
| Async SRAM | 4 KiB | 16 KiB | `AsyncSRAM` at `0x90000000`, size 4 KiB, uncached; `read_cycles=2`, `write_cycles=3` set the byte-lane pin wait. |
| SDRAM | 4 KiB | 0 | `add_sdram(..., origin=0x40000000, size=4 MiB, l2_cache_size=0)` provides `main_ram`; the 50 MHz SoC clock, LiteDRAM model, and PHY clock must agree. |
| SPI Flash | 4 KiB | 16 KiB | A read-only bridge at `0xa0000000`, size 4 KiB, uncached; each CPU load becomes a serial read frame. |

In the SDRAM build, do not add 4 MiB to `integrated_main_ram_size`: `add_sdram` creates the `main_ram` region itself, while the 4 KiB integrated SRAM holds startup stack and runtime data until DRAM initialization finishes. Changing model geometry without changing the mapped size creates a software/hardware capacity mismatch. For the SRAM and Flash builds, `cached=False` keeps each CPU read visible to the bridge and device model; making the region cacheable could hide repeated bus transactions from the protocol checks. Whenever a base or size changes, update the matching linker region and verify that build's generated `csr.csv`.

## 1. Asynchronous SRAM

LiteX `AsyncSRAM` bridges the CPU's Wishbone access to a byte-wide SRAM pin model. A 32-bit write is split across four byte lanes. `ce_n` selects the chip; `we_n` and `oe_n` control writes and reads. The bridge uses `read_cycles=2` and `write_cycles=3`; the whole 32-bit Wishbone transaction takes longer because it performs the lane operations and then acknowledges.

### Why is there an external model if LiteX supplies the bridge?

The LiteX bridge drives the SRAM interface pins, but this test still needs a memory device on the other side of those pins. `async_sram_model.v` stores bytes and responds to chip enable, output enable, write enable, address, and bidirectional data. The two pieces have separate jobs: LiteX translates Wishbone transactions; the Verilog model behaves like the external chip. The run checks full-word and partial-byte writes, the first and last byte, and sequential data.

## 2. SDRAM through LiteDRAM

The model geometry is 4 banks × 2048 rows × 256 columns × 16 bits = 4 MiB. The system clock is 50 MHz. This reduced geometry keeps simulation manageable while retaining SDR SDRAM timing behavior based on `MT48LC4M16`.

### Why initialize SDRAM before using it?

SDRAM powers up requiring a command sequence before reads and writes are valid. Startup first places the stack and C runtime in on-chip SRAM. Firmware then uses LiteDRAM's generated `sdram_phy.h` initialization sequence and gives DFI control back to the controller. Only after the initialization marker does it test DRAM contents. LiteDRAM's controller also schedules refresh; the checker requires at least two refreshes after writes and validates data afterward.

The pinned Python 3.11/Migen combination needs a compatibility helper for CSR variable-name tracing. `sdram/compat.py` adjusts tracing in this process only; the memory controller, PHY model, initialization, and refresh are LiteDRAM components.

## 3. Memory-mapped SPI Flash

The model image is 4 KiB. Its first 256 bytes contain a small project-specific image: `SOCF`, a little-endian length, payload bytes, and a 32-bit byte-sum checksum; the rest is `0xff`. This format is for the experiment, not a general Flash filesystem.

### What happens on a CPU load from Flash?

For each 32-bit Wishbone read, `FlashReadBridge` lowers chip select, shifts out the `0x03` read command and a 24-bit byte address, then clocks in four response bytes. The complete frame contains 8 command bits + 24 address bits + 32 data bits = 64 clocks. The bridge reorders the received bytes into the CPU's little-endian word. The firmware checks the signature, length, checksum, and last word of the 4 KiB window. The Verilog model supports reads only; it does not model erase or programming.

The runner flips one payload bit and runs the same CPU image again. The checksum check must report failure code `0xe3`, with no normal `0x5a` completion. It then restores the good model image.

## Questions and answers

### Are these physical memory chips?

No. The asynchronous SRAM and SPI Flash are pin-level functional Verilog models; SDRAM uses LiteDRAM's SDRAMPHYModel. They let the CPU, bridge/controller, and device protocol interact in simulation. They do not model a board's electrical timing, FPGA pin delays, analog behavior, or a specific chip's full datasheet corners. Physical FPGA/ASIC integration needs device-specific implementations and timing checks.

### Why three different maps?

Each run constructs a different SoC. `0x40000000` refers to the LiteDRAM region in the SDRAM run and to on-chip main RAM in the SRAM and Flash runs. Each generated `csr.csv` is authoritative for its own build. Combining the three maps would assign the same address to incompatible memories.

### What evidence distinguishes bridge/controller behavior from CPU behavior?

The endpoint probes show what the CPU read back. `ASRAM_ACK` and pin-write logs show byte lanes and wait cycles; SDRAM initialization/refresh logs show controller activity; `FLASH_READ` reports each command/address/frame length. A CPU completion marker alone would not show whether the external protocol was correct, so each runner checks both model-level events and firmware readback.

## Dependencies and run

LiteDRAM is an additional dependency. From the repository root, check out the pinned source and run the chapter:

```sh
git clone https://github.com/enjoy-digital/litedram.git external/litedram
git -C external/litedram checkout 74522f715d7b10163ef6f6caa09887a90874be83
git -C external/litedram submodule update --init --recursive
LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py
```

The root runner executes all three configurations in order. You can also run each independently:

```sh
PYTHONHASHSEED=0 python3 chapters/12-memory/async-sram/run.py
LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/sdram/run.py
PYTHONHASHSEED=0 python3 chapters/12-memory/spi-flash/run.py
```

Outputs are kept separately under `results/12-async-sram/`, `results/12-sdram/`, and `results/12-spi-flash/`, including the maps, firmware, logs, initialization files, and VCDs.

## What does a PASS prove?

Each pass proves that firmware accessed its mapped region through the relevant simulated interface and received the expected contents. The SDRAM pass also checks initialization and refresh; the Flash negative case checks data-integrity detection. None of these passes alone proves physical memory timing on a target board.
