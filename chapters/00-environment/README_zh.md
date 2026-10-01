# 00 —— 第一次运行 CPU 前，先弄清哪些工具在做什么

本章固定后续实验使用的软件和硬件工具，并运行 LiteX 自带的 Wishbone 基线测试。通过本章说明主机可以构建和仿真工程；这还不代表 VexiiRiscv 已经执行了固件。

## 我们要让什么运行起来？

项目使用 LiteX 原生的 `vexiiriscv` CPU 封装和 `standard` 变体。封装负责 CPU 与 LiteX SoC 接口之间的连接。VexiiRiscv 的 RTL 由 Scala/SpinalHDL 配置生成；LiteX 不会把 Python 封装直接翻译成 CPU 电路。

```text
VexiiRiscv Scala/SpinalHDL 源码 ── sbt ──> CPU Verilog
RV32 汇编 ── RISC-V GCC ───────────────> 固件镜像
CPU Verilog + LiteX SoC ── Verilator ──> 可执行仿真
```

## 常见问题

### Migen 是 LiteX 的一个模块吗？

Migen 是独立的 Python 硬件描述库。LiteX 建立在 Migen 之上，用 Migen 描述和连接硬件。所以 LiteX 工程会用到 Migen，但它们不是同一个包，安装步骤也不同。仿真时 Python 在构造硬件设计，并不是用 Python 直接解释执行固件。

### 每个工具分别生成什么？

| 工具 | 输入 | 产物或作用 |
| --- | --- | --- |
| `sbt` | VexiiRiscv Scala/SpinalHDL 配置 | CPU RTL，通常是 Verilog |
| RISC-V GCC / `objcopy` | 汇编或 C 固件 | ELF 和可加载到 ROM 的二进制/hex 文件 |
| LiteX / Migen | SoC 参数和硬件模块 | 连接后的 gateware 和软件地址表 |
| Verilator + C++ 编译器 | 生成的 Verilog 和仿真支持代码 | 周期级仿真可执行文件 |

固件编译器不负责构造 CPU；`sbt` 不负责编译固件；Verilator 负责仿真硬件，不是 RISC-V 编译器。

### LiteX 原生支持 VexiiRiscv 吗？

本项目固定的 LiteX 版本包含原生 `VexiiRiscv` CPU 类，注册名为 `vexiiriscv`。用 `cpu_type="vexiiriscv"`、`cpu_variant="standard"` 选择它。`pythondata-cpu-vexiiriscv` 提供封装需要的 CPU 数据和生成器源码。LiteX 与 CPU 源码都固定版本，避免封装和 RTL 的接口悄悄变化。

### 为什么固定这么多版本？

CPU 封装、生成的 RTL、LiteX 仿真 API 和主机编译器需要彼此兼容。跟随最新源码可能在 Python 文件没变的情况下改变接口或工具需求。固定版本能让同一个问题可复现，也方便比较仿真结果。

| 组件 | 固定版本 / 用途 |
| --- | --- |
| LiteX | commit `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| `pythondata-cpu-vexiiriscv` | commit `15cfab529a17c473d0fc75edf3f409eb374cef35` |
| VexiiRiscv generator | commit `235753e24f2d960e49a0852205bae1400bf22c19` |
| Migen / pytest | `migen==0.9.2`、`pytest==9.0.3` |
| LiteX 软件数据包 | `pythondata-software-picolibc==1.7.9.post181`、`pythondata-software-compiler-rt==0.0.post6206`、`pythondata-misc-tapcfg==0.0.post517` |
| Java / sbt | Java 11 或更新版本；Vexii 仓库指定 sbt 1.10.0 |
| Verilator / C++ | Verilator 5 和支持 coroutine 的 C++20 编译器 |
| RISC-V 工具链 | `riscv64-unknown-elf-gcc`、`objcopy`，支持 RV32IM |

## 安装与检查

Debian/Ubuntu 的主机依赖如下。Python 包建议安装在虚拟环境里。

```sh
sudo apt-get update
sudo apt-get install -y build-essential cmake git make pkg-config python3-dev python3-venv \
  libevent-dev libjson-c-dev zlib1g-dev verilator gcc-riscv64-unknown-elf \
binutils-riscv64-unknown-elf openjdk-17-jdk
```

按 [sbt 官方 Linux 安装说明](https://www.scala-sbt.org/download/) 安装 sbt，再从仓库根目录建立固定版本的 Python 和 RTL 环境：

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

VexiiRiscv 仓库通过 `project/build.properties` 指定 sbt 1.10.0。如果 LiteX 放在其他目录，可把 `LITEX_ROOT` 设为 LiteX 源码目录。运行章节时不要更新这些源码；本项目的 CPU 配置会关闭自动更新。

从仓库根目录运行：

```sh
PYTHONHASHSEED=0 python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

检查器把版本、路径、源码提交号和测试输出写到 `results/00/environment.json`。`--wishbone` 运行 LiteX 自带的 Wishbone 基线测试；`--soc` 检查 SoC 和 CPU 导入。`PYTHONHASHSEED=0` 固定当前封装生成 CPU 选项的顺序，方便复用 RTL 缓存。

## PASS 能证明什么？

`PASS 00 Environment and Wishbone baseline` 表示所需工具和固定源码可用，所选基线测试通过。它还不能证明 CPU 复位路径、固件镜像或 SoC 地址图正确。第 01 章才开始提供 CPU 运行证据。
