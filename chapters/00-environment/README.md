# 00 — Host and Source Baseline

## Stage contract

Prepare a Linux host that can generate the pinned VexiiRiscv RTL, compile RV32 firmware, build LiteX simulation RTL, and run the resulting Verilator executable. The verifier records versions and paths in `results/00/environment.json`.

## Required toolchain

| Component | Project requirement |
| --- | --- |
| Python | Python 3.10 or 3.11 with venv support |
| LiteX | Commit `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| Migen / pytest | `migen==0.9.2`, `pytest==9.0.3` |
| pythondata-cpu-vexiiriscv | Package `1.0.1.post325`, source commit `15cfab529a17c473d0fc75edf3f409eb374cef35` |
| VexiiRiscv generator | Commit `235753e24f2d960e49a0852205bae1400bf22c19`, built by sbt |
| LiteX software data | `pythondata-software-picolibc==1.7.9.post181`, `pythondata-software-compiler-rt==0.0.post6206`, `pythondata-misc-tapcfg==0.0.post517` |
| Java / sbt | Java 11 or newer; the VexiiRiscv source pins sbt 1.10.0 for Scala/SpinalHDL RTL generation |
| Verilator / C++ compiler | Verilator 5 and a C++20 compiler with coroutine support |
| RISC-V GNU toolchain | `riscv64-unknown-elf-gcc` and `riscv64-unknown-elf-objcopy`, with RV32IM support |
| Host libraries | `libjson-c-dev`, zlib and libevent development files |

## Host packages

On Debian or Ubuntu, install the host build dependencies and compiler packages:

```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake git make pkg-config python3-dev python3-venv \
  libevent-dev libjson-c-dev zlib1g-dev verilator gcc-riscv64-unknown-elf \
  binutils-riscv64-unknown-elf openjdk-17-jdk
```

Install the sbt launcher using the [official Linux instructions](https://www.scala-sbt.org/download/). The required command must be available as `sbt`; the VexiiRiscv checkout selects sbt 1.10.0 from its `project/build.properties`. Java 11 or newer must be available as `java`. Confirm the distribution's Verilator package supplies version 5 or newer and that `g++ -std=c++20` supports `<coroutine>`.

## Pinned Python and RTL sources

Run from the tour repository root. The following creates a local environment, fetches the pinned source trees, installs the Python packages, and initializes the VexiiRiscv generator checkout:

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

Set the LiteX checkout explicitly when it is not located at `external/litex`:

```sh
export LITEX_ROOT=/absolute/path/to/litex
```

Do not update the pinned checkouts while running a stage. VexiiRiscv's native LiteX wrapper is invoked with repository updates disabled.

## Environment gate

```sh
PYTHONHASHSEED=0 python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

The command checks package imports and versions, source commits, CPU registration, generator files, compiler commands, C++20 support, json-c headers, and LiteX's Wishbone test. It exits nonzero for any missing requirement. The report contains tool paths and test output; it is generated evidence and is not checked into Git.

Stage 01 can begin when this command exits with status 0 and reports `PASS 00 Environment and Wishbone baseline`.
