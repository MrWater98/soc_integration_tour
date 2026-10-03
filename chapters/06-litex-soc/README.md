# 06 — Let LiteX Build the SoC

Stages 01–05 made CPU reset, Wishbone response, ROM image, writable SRAM, and address decode visible one piece at a time. This stage describes the same kind of system with LiteX `SoCCore` and `Builder`, then checks LiteX's generated map against the firmware and runs the CPU.

## What does LiteX take over?

`SoCCore` registers the CPU and establishes common SoC infrastructure: the main bus, integrated ROM/SRAM, CSR access path, and CPU-related regions. `Builder` turns that Python description into gateware, simulator files, address/CSR tables, and software support files. The project still supplies a small completion endpoint so simulation can stop when firmware reaches its pass marker.

```text
soc.py: SoCCore parameters + project endpoint
        │
        ▼
LiteX Builder: gateware, csr.csv/csr.json, simulator project
        │
        ├── check_generated_map: compare hardware map to firmware contract
        └── compile Verilator model → run VexiiRiscv → check SOC_COMPLETE
```

## What does this chapter configure with `SoCCore`?

In this stage, the `SoCCore` configuration grows from the two-instruction CPU test into a mapped SoC with ROM and SRAM. LiteX Builder then exports the resulting address map. The `ProjectSoC` settings match the firmware checks:

| Parameter | Stage 06 value | Why this stage needs it |
| --- | --- | --- |
| `integrated_rom_size` | `0x1000` (4 KiB) | Maps enough ROM to check its first and final words. The reset address remains zero, so the ROM starts at zero. |
| `integrated_rom_init` | `rom_words` (1024 words) | `cpu_sim.py` compiles and pads the image; its last word is `0x5a6b7c8d` for the boundary readback. These are ROM contents, not the ROM address. |
| `integrated_sram_size` | `0x1000` (4 KiB) | Creates LiteX SRAM. `program.S` writes and reads back its first and final words to check the generated region. |
| `integrated_main_ram_size` | `0` | This assembly test accesses SRAM directly and needs no C data section or stack. |
| `with_uart / with_timer / with_ctrl` | All `False` | These peripherals are outside this test, so they are disabled. |
| `ident` | `"SoC Integration Tour Stage 06"` | Identifies this generated SoC build. |

The CPU, reset vector, simulation platform, and clock remain configured in `super().__init__(...)`. `bus_standard` is not specified, so LiteX uses its default Wishbone main bus. VexiiRiscv's peripheral port is AXI-Lite; LiteX inserts `AXILite2Wishbone` when it registers the CPU master.

### Why add a custom `CompletionSlave`?

It is not a standard `SoCCore` peripheral. It is this chapter's simulation-only Wishbone slave: when firmware writes the expected completion code to its mapped address, it prints `SOC_COMPLETE` and ends simulation. That gives the runner evidence that the CPU executed to the firmware check, rather than merely constructing the SoC.

### Why add a custom `CompletionSlave`?

It is not a standard `SoCCore` peripheral. It is this chapter's simulation-only Wishbone slave: when firmware writes the expected completion code to its mapped address, it prints `SOC_COMPLETE` and ends simulation. That gives the runner evidence that the CPU executed to the firmware check, rather than merely constructing the SoC.

## Questions and answers

### Where is `AXILite2Wishbone` called?

It is a native LiteX adapter and is not called directly from any chapter Python file. VexiiRiscv exposes an AXI-Lite peripheral bus. The LiteX `SoCCore` main bus in this setup is Wishbone. While the CPU master is registered, LiteX's `add_master()` / `add_adapter()` path looks up the protocol conversion and instantiates `AXILite2Wishbone` from `litex/soc/interconnect/axi/axi_lite_to_wishbone.py`.

```text
cpu_type="vexiiriscv"
    → native VexiiRiscv wrapper exposes AXI-Lite pBus
    → SoCCore registers cpu_bus0 on its Wishbone main bus
    → LiteX inserts AXILite2Wishbone
    → ROM, SRAM, and project endpoint respond on Wishbone
```

The generated build log reports `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit`. That log line is the direct evidence that LiteX added the bridge in this build. The adapter converts transaction protocol and address representation; it does not decide the software memory map by itself.

### What is `tour_paths.add_litex_to_path`?

It is a project helper in the shared root file `tour_paths.py`, not a LiteX function and not a hardware component. It looks for the LiteX checkout using `LITEX_ROOT` and the project's known source locations, then adds the source root to Python's import path. It does not install LiteX or download source. Each chapter keeps its own logic files; this shared helper only finds the dependency.

### What do the other imported helpers do?

These are project scripts located beside this chapter's `run.py`, not LiteX APIs:

| Helper | Inputs | Work performed | Result |
| --- | --- | --- | --- |
| `build_program(chapter, build_name=...)` in `cpu_sim.py` | This chapter's `program.S` and output name | Calls RISC-V GCC to make an ELF, uses `objcopy` for a flat binary, packs four bytes per little-endian word | `program.elf`, `.bin`, `.hex`, and hash under `results/06/firmware/` |
| `write_rom_init(out, 1024, ...)` in `cpu_sim.py` | Program words and ROM depth | Rejects overflow, pads unused words, adds an optional known final word | A 1024-word `rom_init.hex` and the integer list passed to `SoCCore` |
| `ProjectSoC(platform, rom_words=...)` in `soc.py` | SimPlatform and initialized ROM words | Configures `SoCCore` and attaches the simulation completion slave | A LiteX SoC design description |
| `build_and_run(...)` in `litex_builder.py` | SoC factory, expected map, expected completion text | Calls LiteX Builder, checks generated files, compiles the simulator, runs it, and checks the log | Builder output plus build/compile/run evidence |
| `check_generated_map(csr.csv, regions=...)` | Builder's CSV and expected byte ranges | Compares each generated memory region's origin and size | Continues on a match; raises `AssertionError` on mismatch |

`build_and_run` is a wrapper written for this project; it is not a LiteX API. LiteX's API in that wrapper is `Builder`. Similarly, `build_program` is ordinary Python orchestration around the external RISC-V compiler; it does not compile the CPU hardware.

### Why rebuild firmware after changing the map?

The firmware contains addresses in its instructions. Stage 05 placed SRAM at `0x00010000` and its register endpoint at `0x20000000`. LiteX's generated map in this stage places SRAM at `0x10000000` and the completion endpoint at `0x80000000`. Reusing the old firmware would make it access the wrong regions. This chapter assembles its own `program.S` for the generated LiteX map and compares expected origins and sizes with `csr.csv` before CPU simulation.

### What does `csr.csv` prove, and what does it not prove?

`csr.csv` and `csr.json` show addresses and sizes produced during construction. They prove which map LiteX generated. They do not prove the CPU fetched valid instructions or completed a bus transaction. The `SOC_COMPLETE` write in `run.log` is the runtime evidence that firmware reached the endpoint. The runner also performs a deliberate stale-map check: it expects the old Stage 05 map to be rejected and records the reason in `stale-map.log`.

### Why does the completion log show `0x200003ff`?

The memory map lists byte addresses. The completion endpoint's last byte address is `0x80000fff`, and the firmware writes the final 32-bit word at byte address `0x80000ffc`. On the word-addressed Wishbone trace that is `0x80000ffc / 4 = 0x200003ff`. The log labels this value `word_address` so it is not confused with the software-visible byte address.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py
```

The script runs in this order:

```text
find LiteX source → assemble firmware for this map → create full ROM image
→ instantiate ProjectSoC → run Builder → compare csr.csv to expected regions
→ compile simulator → run CPU → require the expected SOC_COMPLETE log
```

Look at `results/06/builder/csr.csv` for Builder's map, `results/06/memory_map.csv` for the copied map, `build.log` for the AXI-Lite-to-Wishbone adapter message, and `run.log` for CPU observations. `compile.log` captures the simulator build. `builder/gateware/sim.vcd` lets you follow clock/reset, CPU AXI-Lite signals, Wishbone after the adapter, and the completion endpoint.

## What does a PASS prove?

The map check proves the generated LiteX memory regions match the firmware contract. The runtime completion proves the CPU executed the image far enough to write the expected marker through the integrated system. Neither result alone covers board pin constraints, FPGA timing closure, or external memory hardware; those are later project stages.
