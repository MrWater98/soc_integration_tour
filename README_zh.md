# 从头设计验证 SoC

这个项目用 LiteX 和一颗 **VexRiscv**，从最小硬件开始逐步搭出能运行固件的 SoC。基线选择 LiteX 的 `vexriscv/minimal`：RV32I，没有指令缓存和数据缓存。CPU 的取指和数据接口都是 Wishbone，LiteX 把它们接到 SoC 的 Wishbone 互连上。

每一章只增加一个集成点，运行证据保存在 `results/<章节>/`：地址图、固件镜像、仿真日志、波形，以及仿真器实际编译的 RTL。硬件描述生成成功只证明“能构造”；CPU 写出完成码或协议检查器读回预期结果，才证明运行路径成立。

## 当前进度（2026-10-22）

主线已经从 CPU/总线仿真扩展到 **Tang Primer 20K Dock 实物运行，以及 ICS55 ASIC 核心适配和验证实验**。章节内容已补到 20 章，另含 20A DFT 与 CFU、JTAG、SMP 等分支。

- **00–13：** 最小 CPU、存储器和外设集成，走到整机自检与故障回归。
- **13A–13F：** JTAG、边界扫描、OpenOCD、GDB、工具比较和神经网络算子加速。GDB 目前调试本机程序，尚未通过 JTAG 控制 SoC CPU。
- **14–17：** Tang 的开源构建和真实板卡运行。已有 54 MHz 连续 600 秒、10 次热复位及 27 MHz 连续 120 秒记录；17A/B 的 SMP 已通过 RTL 仿真，上板待做。
- **18–20A：** ICS55 最小工艺流程、无缓存 RV32I 核心的工艺映射/功能仿真、故障与覆盖验证、扫描和 RAM March 教学实验。真实 SRAM 宏、生产 DFT、物理设计及流片签核继续按 PLAN 推进。

先看[整个项目的进度与结果解读](docs/progress/README.md)，再看[完整路线](PLAN.md)。[同步验收记录](docs/progress/VALIDATION.md)区分了导入的历史结果和本次在 tour 本地重跑的实验。原有 00–12 章本次未逐项重跑。PLAN_zh.md 是旧版计划，当前路线以 PLAN.md 为准。

## 章节和运行入口

从仓库根目录运行。生成文件统一写到 `results/`。

| 章 | 实验内容 | 运行命令 |
| --- | --- | --- |
| 00 环境 | Python、LiteX、VexRiscv RTL、Verilator 和工具链检查 | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU 启动 | 复位、取指、第一次 Wishbone 写入和无 ACK | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | 应答时序与失效场景 | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | 汇编程序并从 ROM 镜像启动 | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | 字节通道、栈存储和越界访问 | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 地址图 | 地址区域、重叠和未映射访问 | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`、`Builder`、地址图与 Wishbone 设备 | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 裸机 C | 启动代码、`.data`、`.bss` 和栈 | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | 用 CSR 控制输出和读取输入 | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | UART FIFO 和 8N1 引脚波形 | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 定时器中断 | Timer 轮询、机器外部中断和 ISR 返回 | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI / I2C | 控制器事务与 NACK 处理 | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 外部存储器 | 异步 SRAM、SDRAM 和 SPI Flash 配置 | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

CPU RTL 由固定版本的 `pythondata-cpu-vexriscv` Python 包提供，不需要用 Scala/SBT 生成 CPU。GCC 编译固件，LiteX/Migen 组装 SoC，Verilator 编译周期级仿真器。

## 硬件路径

```text
VexRiscv 取指 Wishbone ─┐
                        ├─ LiteX 共享 Wishbone ─ ROM / SRAM / CSR / 外设
VexRiscv 数据 Wishbone ─┘

RISC-V 汇编/C ─ GCC + objcopy ─ 固件镜像
LiteX + Migen ─ Builder ─ RTL 和地址图
Verilator + C++ ─ 周期级仿真
```

## 后续章节与阅读入口

| 章 | 主题 | 学什么 |
| --- | --- | --- |
| 13 | [整机集成与故障回归](chapters/13-integration/README.md) | CPU 自检、外设并发、错误 CSR/IRQ 和损坏 ROM |
| 13A | [JTAG / TAP](chapters/13a-jtag-tap/README.md) | 从引脚时序理解捕获、移位、更新与状态机 |
| 13B | [边界扫描](chapters/13b-boundary-scan/README.md) | 采样输入、接管输出、连接故障实验 |
| 13C | [OpenOCD](chapters/13c-openocd/README.md) | 真实软件经 remote_bitbang 操作仿真 TAP |
| 13D | [GDB](chapters/13d-gdb/README.md) | 本机递归程序的断点、栈和寄存器观察 |
| 13E | [仿真工具比较](chapters/13e-tool-comparison/README.md) | 工具能力、适用范围与运行记录 |
| 13F | [神经网络算子加速（选学）](chapters/13f-cfu-ml/README.md) | 原版 CFU、INT8 点积、真实自定义指令调用及软硬件对照 |
| 14 | [Tang FPGA 平台](chapters/14-fpga-platform/README.md) | 时钟、引脚、CSR、C 固件和生成文件逐步讲解 |
| 14E | [布局布线参数实验](chapters/14e-seed-sweep/README.md) | seed、RAM 容量、算法和时序权重 |
| 15 | [开源 FPGA 构建](chapters/15-fpga-build/README.md) | Yosys → nextpnr → Apicula → .fs |
| 16 | [真实上板](chapters/16-board-smoke/README.md) | WSL USB、JTAG 下载、LED、UART 和复位 |
| 17 | [板上稳定性](chapters/17-fpga-stability/README.md) | RAM 事务计数、IRQ、串口、连续运行和热复位 |
| 17A | [SMP 单 hart](chapters/17a-smp-single/README.md) | 真实 SMP RTL 的独立栈、原子访问和 CLINT |
| 17B | [SMP 双 hart](chapters/17b-smp-dual/README.md) | 共享 RAM、邮箱、原子计数和失效用例 |
| 18 | [ICS55 PDK 与最小映射](chapters/18-ics55-spec/README.md) | 固定工艺版本、标准单元映射、门级仿真和单角 STA |
| 19 | [ASIC RTL 适配](chapters/19-asic-rtl/README.md) | 小型 RV32I SoC、存储清单、常量 ROM 和触发器 RAM |
| 20 | [ASIC 验证工作包](chapters/20-asic-verification/README.md) | 故障、复位、随机事务、有限步形式检查、lint 和行覆盖 |
| 20A | [DFT 入门](chapters/20a-dft-basics/README.md) | 内部扫描、RAM March 与可列举故障检测 |

## 文件怎样产生，先看什么？

```text
main.c + startup.S + linker.ld ─ GCC ─ 固件镜像 / 地址映射 / 反汇编
LiteX Python + 自带 RTL ─ Migen / Builder ─ SoC RTL + ROM 初始化 + CSR 头文件
                                          │
                         ┌────────────────┴─────────────────┐
                         ▼                                  ▼
                    仿真与故障注入                  综合 / FPGA 布局布线
                         │                                  │
                    日志、CSV、覆盖率                 网表、时序报告、.fs
```

章节源码和解释在 `chapters/`，生成输入快照在 `results/<实验>/rtl/`；`.init` 也是 RTL 仿真输入的一部分。读结果先找 `summary.json` 或 `REPORT.md`，再对照日志与固件反汇编。具体生成关系见[LiteX 生成文件说明](docs/generated-files/README.md)。大体积波形和编译中间文件运行后生成，未全部随仓库保存。

CPU 配置随实验变化：00–12 的基线是 `minimal`，CFU 实验使用 `full+cfu`，SMP 另有配置，19 章又收敛到无缓存 RV32I 小核心。上图的共享 Wishbone 是基线示意；19 章使用 crossbar。GPIO 位数、RAM 大小、频率和超时计数都是当前配置的选择，阅读时应找到参数定义。

## 检查与重放

从仓库根目录执行，依赖安装方法见各章：

```sh
# 核对导入文件哈希、Python 语法、RTL 初始化文件与工具位置。
python3 tools/check_progress.py

# 用随附快照重放 19/20 的六个选定检查，需要 Icarus Verilog。
python3 tools/verify_import.py

# 独立的扫描与 RAM March 实验，需要 Icarus Verilog。
python3 chapters/20a-dft-basics/run.py --output results/20a-local
```

本次重放中，19 章 RTL、通用网表、ICS55 工艺网表均成功启动；20 章两次启动通过，缺失 ACK 和错误 GPIO 被正确检出。CFU 与 DFT 小实验也已在 tour 本地重跑通过。完整 20 章回归、工艺重新映射及板上重新下载可按各章入口执行。
