# 00 — What do we need before the first run?

This chapter pins LiteX, VexRiscv RTL, and simulation tools, then runs LiteX's Wishbone baseline test. Passing means the host can build the project; it does not yet prove that the CPU has executed firmware.

## What are we building?

The project uses LiteX's native `vexriscv` wrapper with its `minimal` variant. LiteX loads the pre-generated `VexRiscv_Min.v` from `pythondata-cpu-vexriscv`; this flow does not need Scala or SBT to generate the CPU.

```text
RISC-V assembly/C ─ GCC ───────────> firmware image
LiteX + Migen ─ Builder ────────────> SoC RTL and software maps
SoC RTL + Verilator/C++ ────────────> cycle-level simulator
```

## Questions and answers

### Is Migen part of LiteX?

Migen is a separate Python hardware-description library. LiteX is built on it and uses it to describe and connect hardware. Python generates the hardware structure; VexRiscv executes the firmware on the generated SoC.

### What does each tool do?

| Tool | Input | Output / job |
| --- | --- | --- |
| RISC-V GCC / `objcopy` | Assembly or C firmware | ELF, binary, and ROM image |
| LiteX / Migen | SoC parameters and hardware modules | Connected gateware and software maps |
| Verilator + C++ compiler | Generated Verilog and simulator support code | Cycle-level simulator |

The firmware compiler does not build the CPU. Verilator does not compile RISC-V firmware.

### Why pin versions?

The LiteX wrapper, CPU RTL, simulation API, and host compiler must work together. Fixed versions make failures reproducible and let us compare generated results across chapters.

| Component | Pinned version / use |
| --- | --- |
| LiteX | Commit `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| `pythondata-cpu-vexriscv` | Commit `642ecfed1c84460555d6d803d660cc60cfc1ecb6` |
| Migen / pytest | `migen==0.9.2`, `pytest==9.0.3` |
| LiteX software data | picolibc `1.7.9.post181`, compiler-rt `0.0.post6206`, tapcfg `0.0.post517` |
| Verilator / C++ | Verilator 5 or newer and a C++ compiler |
| RISC-V tools | `riscv64-unknown-elf-gcc` and `objcopy` supporting RV32I/ILP32 |

### How do I install the dependencies?

On Debian or Ubuntu, install the host tools and use a Python virtual environment for packages:

```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake git make pkg-config python3-dev python3-venv \
  libevent-dev libjson-c-dev zlib1g-dev verilator gcc-riscv64-unknown-elf \
  binutils-riscv64-unknown-elf
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
mkdir -p external
git clone https://github.com/enjoy-digital/litex.git external/litex
git -C external/litex checkout aa32cc0d4952f0959afa0f8c16de2fd840128033
python -m pip install -e external/litex migen==0.9.2 pytest==9.0.3
git clone https://github.com/litex-hub/pythondata-cpu-vexriscv.git external/pythondata-cpu-vexriscv
git -C external/pythondata-cpu-vexriscv checkout 642ecfed1c84460555d6d803d660cc60cfc1ecb6
python -m pip install -e external/pythondata-cpu-vexriscv
python -m pip install pythondata-software-picolibc==1.7.9.post181 pythondata-software-compiler-rt==0.0.post6206 pythondata-misc-tapcfg==0.0.post517
```

If LiteX is outside the paths checked automatically, set `LITEX_ROOT` to its source directory. Do not update pinned source checkouts while running a chapter.

### How do I check the setup?

```sh
python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

`--strict` fails on missing requirements or version mismatches; `--wishbone` runs LiteX's Wishbone tests; `--soc` checks SoCCore/Builder Python dependencies. The report at `results/00/environment.json` records versions, paths, and test output.
