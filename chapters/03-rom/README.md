# 03 — From Assembly to a Running ROM Image

Stage 01 returned instructions from a small inline list. This stage builds the firmware with the RISC-V toolchain, packs a complete initialized ROM, checks the memory map, and boots the same native VexiiRiscv CPU from reset address zero.

## How does assembly become ROM contents?

```text
program.S
   │ riscv64-unknown-elf-gcc (-march=rv32im -mabi=ilp32, linked at 0)
   ▼
program.elf ── objcopy -O binary ──> program.bin (bytes)
                                      │ group every 4 bytes, little-endian
                                      ▼
                                 program.hex (32-bit words)
                                      │ pad to 256 words with NOPs
                                      ▼
                                 rom_init.hex (complete 1 KiB image)
                                      │ integrated_rom_init
                                      ▼
                           LiteX ROM → VexiiRiscv instruction fetch
```

The code is linked to address `0x0`, because the CPU reset address is `0x0` and the ROM begins there. `rv32im` selects the instruction set and `ilp32` the 32-bit ABI. These are software build settings and must be supported by the generated CPU; changing the ISA flags alone can produce instructions the core cannot execute. The compiler builds software; it does not generate CPU RTL.

## What does LiteX do at this stage?

`ProjectSoC` still inherits from `SoCCore`: LiteX supplies the CPU, Wishbone main bus, CSR structure, and ROM bus. This chapter passes the compiled `words` as `integrated_rom_init` and sets ROM capacity to `len(words) * 4`. Image length, ROM capacity, reset address, and link address form one contract: this experiment chooses 256 words (1024 bytes), the reset PC is zero, and the firmware is linked at zero. ROM depth is configurable; if it changes, update `ROM_WORDS`, the image padding/overflow checks, and the expected generated region along with the image.

The completion endpoint is a project-written Wishbone slave. `self.add_module(...)` registers the Migen module, `self.bus.add_slave(...)` connects its interface to the main bus, and `SoCRegion` declares `0x20000000–0x20000fff`; `SoCIORegion` registers the CPU I/O range. `cached=False` marks this side-effecting MMIO endpoint as non-cacheable. `Builder(..., compile_software=False)` builds gateware and the simulator only; `cpu_sim.py` controls software compilation separately, making the ELF, binary image, and boundary checks easy to inspect.

## Questions and answers

### Why are there several image files?

`program.elf` includes executable sections and symbol information useful for debugging. `program.bin` is a flat byte sequence extracted from the ELF. This chapter's `program.hex` writes those bytes as one 32-bit hexadecimal word per line so Python can inspect and pack them. `rom_init.hex` has exactly 256 words, including NOP fill, because the ROM is 256 × 4 = 1024 bytes. SHA-256 files identify the generated inputs and image.

### What does little-endian packing mean?

The least significant byte is stored at the lowest address. If the four bytes are `b7 02 00 20`, the 32-bit word is `0x200002b7`. The helper converts each 4-byte group using little-endian order and checks that converting the words back reproduces the padded bytes. That catches a byte-order or packing mistake before simulation.

### What does the memory map describe?

It is the agreement between a CPU-visible byte address and the hardware region that responds there. It does not itself create hardware decode logic; LiteX's bus and regions or a project decoder must implement the agreement.

| Region | Byte address range | Use |
| --- | --- | --- |
| ROM | `0x00000000–0x000003ff` | Reset code and firmware, 1 KiB |
| Completion endpoint | `0x20000000–0x20000fff` | Simulation register that records firmware's `0x35` pass marker |
| CSR | `0xf0000000–0xf000ffff` | LiteX control/status register space |

The software map uses byte addresses. On this 32-bit word-addressed Wishbone bus, byte address `0x20000000` is word address `0x08000000`. Keep these units explicit when comparing the firmware, generated map, and bus trace.

### How do we know the CPU ran the program?

The runner checks that the ROM image is nonempty and no larger than 256 words, and that the reset address is aligned and inside the ROM. It also checks the generated map before simulation. During simulation the CPU must fetch at address zero and the completion endpoint must receive `0x35` and acknowledge it. The completion write is runtime evidence; a successful image build or a generated map alone only proves construction and configuration.

### Why test the boundary and invalid configurations?

An image with 257 words cannot fit in this ROM; a reset address of `0x1000` is just beyond its last byte, and reset address 1 is unaligned. These are rejected before CPU simulation. The test keeps capacity and reset-vector mistakes from appearing later as vague instruction-fetch failures.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/03-rom/run.py
```

Inspect `results/03/program.elf`, `program.bin`, `program.hex`, `rom_init.hex`, the image hashes, `memory_map.csv`, `run.log`, and the generated VCD. The firmware writes `0x35`; the endpoint prints `SOC_COMPLETE` only after receiving that value. A fetch at zero shows the reset path reached ROM, while the completion marker shows firmware reached the end of this short test.

## What does a PASS prove?

The pass proves that this assembled image fits the configured ROM, the reset and map checks agree with the SoC, and VexiiRiscv executes far enough to make the expected completion write. Stage 04 adds writable memory and exercises SRAM byte lanes and stack storage.
