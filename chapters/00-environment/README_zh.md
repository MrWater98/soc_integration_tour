# 00 — 主机与源码基线

## 阶段合同

准备 Linux 主机，使其能够生成固定版本的 VexiiRiscv RTL、编译 RV32 固件、构建 LiteX 仿真 RTL，并运行 Verilator 仿真程序。检查器把版本和路径写入 `results/00/environment.json`。

## 所需工具

| 组件 | 项目要求 |
| --- | --- |
| Python | Python 3.10 或 3.11，支持 venv |
| LiteX | 提交 `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| Migen / pytest | `migen==0.9.2`、`pytest==9.0.3` |
| pythondata-cpu-vexiiriscv | 包版本 `1.0.1.post325`，源码提交 `15cfab529a17c473d0fc75edf3f409eb374cef35` |
| VexiiRiscv 生成器 | 提交 `235753e24f2d960e49a0852205bae1400bf22c19`，由 sbt 构建 |
| LiteX 软件数据包 | `pythondata-software-picolibc==1.7.9.post181`、`pythondata-software-compiler-rt==0.0.post6206`、`pythondata-misc-tapcfg==0.0.post517` |
| Java / sbt | Java 11 或更新版本；VexiiRiscv 源码通过 sbt 1.10.0 构建 Scala/SpinalHDL RTL |
| Verilator / C++ | Verilator 5 和支持 coroutine 的 C++20 编译器 |
| RISC-V GNU 工具链 | `riscv64-unknown-elf-gcc` 与 `objcopy`，支持 RV32IM |
| 主机库 | `libjson-c-dev`、zlib 和 libevent 开发文件 |

## Linux 主机依赖

Debian 或 Ubuntu 可使用以下命令安装系统依赖和交叉编译器：

```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake git make pkg-config python3-dev python3-venv \
  libevent-dev libjson-c-dev zlib1g-dev verilator gcc-riscv64-unknown-elf \
  binutils-riscv64-unknown-elf openjdk-17-jdk
```

sbt launcher 按[官方 Linux 安装说明](https://www.scala-sbt.org/download/)安装。要求命令名为 `sbt`；VexiiRiscv checkout 会从 `project/build.properties` 选择 sbt 1.10.0。Java 11 或更新版本的命令名为 `java`。确认 Verilator 为 5 或更新版本，并确认 `g++ -std=c++20` 可编译 `<coroutine>`。

## 固定 Python 和 RTL 源码

在 tour 仓库根目录运行以下命令。它创建本地虚拟环境、检出固定源码、安装 Python 包并初始化 VexiiRiscv 生成器：

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

LiteX 不在 `external/litex` 时，显式指定源码目录：

```sh
export LITEX_ROOT=/absolute/path/to/litex
```

运行阶段命令时不要更新固定源码。LiteX 的 VexiiRiscv 封装会关闭运行时仓库更新。

## 环境门禁

```sh
PYTHONHASHSEED=0 python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

命令检查 Python 包、源码提交、CPU 注册、生成器文件、编译器、C++20、json-c 头文件和 LiteX Wishbone 测试。任何必需项缺失都会返回非零。报告包含工具路径和测试输出，属于生成产物，不提交到 Git。

命令返回 0 且输出 `PASS 00 Environment and Wishbone baseline` 后，可进入阶段 01。
