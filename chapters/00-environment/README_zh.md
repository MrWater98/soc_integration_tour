# 00 —— 第一次运行前需要什么？

本章固定 LiteX、VexRiscv RTL 和仿真工具版本，并运行 LiteX 自带的 Wishbone 基础测试。通过本章表示主机环境可以构建项目；它还不证明 CPU 已运行固件。

## 我们要运行什么？

项目使用 LiteX 原生 `vexriscv` wrapper 的 `minimal` 变体。LiteX 从 `pythondata-cpu-vexriscv` 包加载预生成的 `VexRiscv_Min.v`；教程不需要 Scala/SBT 去生成 CPU。

```text
RISC-V 汇编/C ─ GCC ──────────────> 固件镜像
LiteX + Migen ─ Builder ───────────> SoC RTL 和地址图
SoC RTL + Verilator/C++ ───────────> 周期级仿真器
```

## 问答

### Migen 是 LiteX 的一部分吗？

Migen 是独立的 Python 硬件描述库。LiteX 构建在 Migen 之上，用它描述和连接硬件。运行时 Python 负责生成硬件结构；固件是在生成后的 SoC 上由 VexRiscv 执行的。

### 每种工具负责什么？

| 工具 | 输入 | 产物/职责 |
| --- | --- | --- |
| RISC-V GCC / `objcopy` | 汇编或 C 固件 | ELF、二进制和 ROM 镜像 |
| LiteX / Migen | SoC 参数和硬件模块 | 互连后的 gateware 与软件地址图 |
| Verilator + C++ 编译器 | 生成的 Verilog 和仿真支持代码 | 周期级仿真器 |

固件编译器不负责构造 CPU；Verilator 不编译 RISC-V 固件。

### 为什么要固定版本？

LiteX wrapper、CPU RTL、仿真 API 和主机编译器必须兼容。固定版本能让构建失败可复现，也便于比较不同章节生成的结果。

| 组件 | 固定版本/用途 |
| --- | --- |
| LiteX | commit `aa32cc0d4952f0959afa0f8c16de2fd840128033` |
| `pythondata-cpu-vexriscv` | commit `642ecfed1c84460555d6d803d660cc60cfc1ecb6` |
| Migen / pytest | `migen==0.9.2`、`pytest==9.0.3` |
| LiteX 软件数据 | picolibc `1.7.9.post181`、compiler-rt `0.0.post6206`、tapcfg `0.0.post517` |
| Verilator / C++ | Verilator 5 或更新版本、C++ 编译器 |
| RISC-V 工具 | `riscv64-unknown-elf-gcc` 和 `objcopy`，支持 RV32I/ILP32 |

### 怎么安装？

Debian/Ubuntu 主机可以安装这些系统工具；Python 包使用虚拟环境隔离：

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

若 LiteX 源码不在自动查找位置，设置 `LITEX_ROOT` 指向它。不要在运行章节时更新固定源码。

### 怎么检查？

```sh
python3 chapters/00-environment/check_env.py --strict --wishbone --soc
```

`--strict` 会在必需项缺失或版本不符时返回失败；`--wishbone` 运行 LiteX 的 Wishbone 测试；`--soc` 检查 SoCCore/Builder 的 Python 依赖。详细版本、路径与测试输出写到 `results/00/environment.json`。
