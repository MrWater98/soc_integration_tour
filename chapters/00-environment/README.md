# 00 — Questions Before the First CPU Run

This chapter fixes the software and hardware tools used by the later stages. It also runs LiteX's own Wishbone baseline test. Passing this stage means the host can build and simulate the project; it does not mean that VexiiRiscv has executed firmware yet.

## What are we trying to make run?

The project uses LiteX's native `vexiiriscv` CPU wrapper and the `standard` variant. The wrapper connects the CPU to LiteX's SoC interfaces. VexiiRiscv's RTL is generated from Scala/SpinalHDL sources; LiteX does not translate the Python CPU wrapper into CPU logic.

```text
VexiiRiscv Scala/SpinalHDL source ── sbt ──> generated CPU Verilog
RV32 assembly ── RISC-V GCC ──────────────> firmware image
CPU Verilog + LiteX SoC ── Verilator ─────> executable simulation
```

## Questions and answers

### Is Migen part of LiteX?

Migen is a separate Python-based hardware-description library. LiteX is built on Migen and uses it to describe and connect hardware. A LiteX SoC can use Migen modules, but installing LiteX and Migen are distinct package steps. In the simulation, Python builds a hardware design; it is not running the firmware as ordinary Python code.

### What does each tool produce?

| Tool | Input | Output / job |
| --- | --- | --- |
| `sbt` | VexiiRiscv Scala/SpinalHDL configuration | CPU RTL, usually Verilog |
| RISC-V GCC / `objcopy` | Assembly or C firmware | ELF and ROM-ready binary/hex files |
| LiteX / Migen | SoC parameters and hardware modules | Connected gateware and generated software maps |
| Verilator + C++ compiler | Generated Verilog and simulator support code | Executable cycle-level simulation |

The firmware compiler does not build the CPU. `sbt` does not compile the firmware. Verilator simulates the resulting hardware; it is not the RISC-V compiler.

### Does LiteX support VexiiRiscv natively?

The pinned LiteX revision includes a `VexiiRiscv` CPU class registered as `vexiiriscv`. The project selects it with `cpu_type="vexiiriscv"` and `cpu_variant="standard"`. The `pythondata-cpu-vexiiriscv` package supplies the CPU data and generator checkout expected by that wrapper. Pinning both LiteX and the CPU source keeps the wrapper and generated RTL reproducible.

### Why pin so many versions?

The CPU wrapper, generated RTL, LiteX simulation API, and host compiler must agree. A moving source checkout can change generated interfaces or tool requirements without changing this project's Python code. The pins in the table below make a failure repeatable and make generated results comparable.

| Component | Pinned requirement / use |
| --- | --- |
| LiteX | Commit `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| `pythondata-cpu-vexiiriscv` | Commit `15cfab529a17c473d0fc75edf3f409eb374cef35` |
| VexiiRiscv generator | Commit `235753e24f2d960e49a0852205bae1400bf22c19` |
| Migen / pytest | `migen==0.9.2`, `pytest==9.0.3` |
| LiteX software data | `pythondata-software-picolibc==1.7.9.post181`, `pythondata-software-compiler-rt==0.0.post6206`, `pythondata-misc-tapcfg==0.0.post517` |
| Java / sbt | Java 11 or newer; Vexii checkout selects sbt 1.10.0 |
| Verilator / C++ | Verilator 5 and a C++20 compiler with coroutine support |
| RISC-V tools | `riscv64-unknown-elf-gcc` and `objcopy`, with RV32IM support |

## Install and check

On Debian or Ubuntu, install the host tools shown below. Use a virtual environment for Python packages.

```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake git make pkg-config python3-dev python3-venv \
  libevent-dev libjson-c-dev zlib1g-dev verilator gcc-riscv64-unknown-elf \
binutils-riscv64-unknown-elf openjdk-17-jdk
```

Install sbt using its [official Linux instructions](https://www.scala-sbt.org/download/), then create the pinned Python and RTL environment from the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
mkdir -p external
git clone https://github.com/enjoy-digital/litex.git external/litex
git -C external/litex checkout aa32cc0d4952f0959afa0f8c16de2fd840128033
python -m pip install -e external/litex migen==0.9.2 pytest==9.0.3
git clone https://github.com/litex-hub/pythondata-cpu-vexiiriscv.git external/pythondata-cpu-vexiiriscv
git -C external/pythondata-cpu-vexiiriscv checkout 15cfab529a17c473d0fc75edf3f409eb374cef35
git -C external/pythondata-cpu-vexiiriscv submodule update --init --recursive
python -m pip install -e external/pythondata-cpu-vexiiriscv
git -C external/pythondata-cpu-vexiiriscv/pythondata_cpu_vexiiriscv/verilog/ext/VexiiRiscv checkout 235753e24f2d960e49a0852205bae1400bf22c19
python -m pip install pythondata-software-picolibc==1.7.9.post181 pythondata-software-compiler-rt==0.0.post6206 pythondata-misc-tapcfg==0.0.post517
```

The VexiiRiscv checkout selects sbt 1.10.0 through `project/build.properties`. If LiteX lives elsewhere, set `LITEX_ROOT` to its source directory. Do not update these checkouts while running a stage; the chapter CPU setup disables repository updates.

Run from the repository root:

```sh
PYTHONHASHSEED=0 python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

The checker records versions, paths, source revisions and test output in `results/00/environment.json`. `--wishbone` runs LiteX's Wishbone baseline test; `--soc` checks the required SoC and CPU imports. `PYTHONHASHSEED=0` stabilizes generated CPU option ordering for this pinned wrapper and its RTL cache.

## What does a PASS prove?

`PASS 00 Environment and Wishbone baseline` proves that the checked host tools and pinned sources are available and LiteX's selected baseline test passes. It does not prove that the project CPU reset path, firmware image, or SoC memory map works. Stage 01 supplies the first CPU-level evidence.

## Read next

Stage 01 instantiates VexiiRiscv and observes its first fetch and store. Stage 02 removes the CPU temporarily and examines Wishbone requests and responses one cycle at a time.
