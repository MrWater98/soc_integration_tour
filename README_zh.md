# 从头设计验证 SoC

这个项目用 LiteX 和一颗 VexiiRiscv，从最小硬件开始搭一套能运行固件的 SoC。每章提出一个问题，用小实验回答它：先看 CPU 是否取指，再看总线怎样应答、程序如何进入 ROM、RAM 和地址图怎样加入，最后交给 LiteX 构造 SoC，并继续接入常见外设与外部存储器。

## 为什么不一开始就拼完整 SoC？

Litex、HeteroSoC 或 Chipyard 都能快速拼出能运行的系统。我更想知道每个部件的最小构造和最小验证是什么：CPU 参数怎样选，总线请求由谁回答，汇编怎样变成 ROM 镜像，一个软件地址怎样到达目标设备。把这些边界拆开后，失败时能知道自己在查 CPU、固件、总线，还是地址图。

实验会留下地址表、编译产物、逐周期日志和波形。构建成功只说明硬件描述能生成；CPU 完成一次写入或协议检查器读回正确值，才是运行证据。负例也要有明确预期：例如没有 ACK 应该超时，未映射地址应该触发访问异常。

## 章节进度与运行入口

从仓库根目录运行。生成文件统一写到被 Git 忽略的 `results/` 下。

| 章 | 实验问题 | 运行命令 |
| --- | --- | --- |
| 00 环境 | 哪些工具生成 CPU、固件和仿真器？ | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU 启动 | VexiiRiscv 能否退出复位、取指并发出指定写入？ | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | 一笔请求怎样完成？缺 ACK、早 ACK、悬挂 ACK 如何被捕获？ | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | 汇编、ELF、字节、32 位字、复位地址和 ROM 容量怎样对应？ | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | RAM 如何支持读写、字节通道、函数栈帧和返回？ | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 地址图 | 一个地址由哪个设备响应？重叠和空洞会怎样？ | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`、`Builder` 和 AXI-Lite/Wishbone 桥分别做什么？ | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 裸机 C | 启动代码如何初始化 `.data`、`.bss` 并进入 C？ | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | CPU 如何通过 CSR 控制输出、读取输入？ | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | CSR 写入如何变成串口引脚上的 8N1 波形？ | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 定时器中断 | 外设事件怎样经过 PLIC 进入 ISR 并返回？ | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI / I2C | 总线控制器能否按协议完成读写并检测 NACK？ | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 外部存储器 | 并行 SRAM、SDRAM 和 SPI Flash 的访问路径有何不同？ | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

00–12 均有独立章节说明与运行入口。第 12 章另需按该章说明检出固定版本 LiteDRAM。13–15 仍是集成回归和 FPGA 实测计划。

## 从源码到总线应答

```text
VexiiRiscv Scala/SpinalHDL ── sbt ───────> CPU Verilog
RISC-V C / 汇编 ──────────── GCC/objcopy ─> ELF / ROM 镜像
LiteX SoCCore + Migen 模块 ─ Builder ─────> SoC gateware / 地址表
CPU AXI-Lite 外设口 ── AXILite2Wishbone ──> Wishbone 主总线
                                               ├── ROM
                                               ├── SRAM / 外部存储控制器
                                               └── CSR / 项目端点
Verilator + C++ ──────────────────────────> 周期级仿真
```

这条流程里有几种不同的“构建”：`sbt` 生成 CPU RTL，RISC-V GCC 编译软件，LiteX/Migen 组装 SoC，Verilator 编译仿真器。它们产物不同，不能互相替代。

## 常见问题

### Migen 是 LiteX 的一个模块吗？

Migen 是独立的 Python 硬件描述库，LiteX 建立在 Migen 之上。Migen 提供信号、模块和时序逻辑的描述方式；LiteX 在此基础上提供 CPU、总线、存储器、CSR、Builder 等 SoC 组件。它们是不同的软件包。

### LiteX 原生支持 VexiiRiscv 吗？

本项目固定的 LiteX 版本包含原生 `VexiiRiscv` 封装，注册名为 `vexiiriscv`，本项目选择 `standard` 变体。LiteX 封装负责把 CPU 接到 SoC；VexiiRiscv 的 Scala/SpinalHDL 生成器负责产生 CPU RTL，`sbt` 运行生成流程。`pythondata-cpu-vexiiriscv` 提供封装所需的 CPU 数据和生成器源码。

### `AXILite2Wishbone` 是项目自己写的吗？为什么 Python 里找不到它？

它是 LiteX 自带的桥。VexiiRiscv 的外设总线是 AXI-Lite，而本系统的主总线是 Wishbone。LiteX 注册 CPU master 时发现两端协议不同，会在构建过程中自动插入 `AXILite2Wishbone`。所以项目代码负责选 CPU、建 SoC 和接从设备，不需要自己实例化协议桥。第 06 章的 `build.log` 会记录适配信息。

### 为什么有的地址差四倍？字节、字和字节通道是什么关系？

程序和 LiteX memory map 用字节地址。32 位 Wishbone 若按字寻址，每个地址单位表示 4 个字节，所以软件地址 `0x40` 在总线上可能显示为字地址 `0x10`。数据仍是 `0x40`，变的是地址的计量单位。`sel` 则是 4 个 byte-enable 位，决定这个 32 位字里哪些字节参与读写。

### Wishbone 的 ACK 为什么重要？怎么知道故障发生在哪里？

`cyc/stb` 表示请求有效，`ack` 表示从设备确认本次访问完成。总线上即使有读数据，没有 ACK 也不能当作成功读回。第 02 章逐拍采集地址、请求、ACK 和数据到 CSV/VCD：无应答在限定周期内超时；提前 ACK 在请求前就被抓到；悬挂 ACK 在主设备撤销请求后被抓到；未映射地址则显示请求地址不属于从设备范围。检查器给出判定，波形保留判定依据，因此不是只凭一次模糊的仿真超时猜原因。

### 汇编怎样真正进入 ROM？`memory_map` 又做什么？

RISC-V GCC 先把汇编链接成 ELF；`objcopy` 提取连续二进制字节；项目脚本按小端序每 4 字节合成一个 32 位 ROM 字，并补齐 ROM 深度。CPU 从复位地址取 ROM 指令。`memory_map` 记录字节地址对应的硬件区域，检查器核对起点、容量、对齐和重叠；真正的地址译码由 SoC 总线区域实现，单独一张表不会凭空生成硬件。

### `sp` 是什么？`ra` 又为什么要保存？

`sp` 是通用寄存器 `x2`，里面放着当前栈帧边界的 RAM 字节地址；它不是函数地址，也不会自动指向函数开头。软件通过修改 `sp` 在 RAM 里给当前调用留出空间，再用偏移访问帧里的局部数据和保存值。`ra` 是寄存器 `x1`：`jal` 把下一条指令地址写进 `ra` 并跳转。嵌套调用会覆盖 `ra`，所以仍需返回的函数先把旧值存到自己的栈帧，再在返回前恢复。硬件只执行 `addi`、`sw`、`lw`、`jal`、`jalr`；压栈和栈帧是软件约定。第 04 章用 `fact(3)` 的逐层表格展示 `sp`、`ra` 和栈内存的变化。

### 这里的 SRAM 是真实芯片吗？为什么有时还需要 testbench 模型？

LiteX 的 `wishbone.SRAM` 是 SoC 内部的行为存储器，适合验证总线接线、读写、byte enable 和软件访问。第 04 章测试的对象就是这块 LiteX SRAM，因此不需要在 `tb.sv` 再造一份相同存储器。第 12 章的异步 SRAM 则位于 LiteX 总线桥外侧：LiteX 桥只驱动 SRAM 芯片引脚，Verilog 模型负责在引脚另一侧保存字节并响应读写。两种模型处在不同的接口边界。

FPGA 通常把综合推断的存储器映射到片上 block RAM；ASIC 则常用 SRAM 硬宏。真实 SRAM 宏一般没有 Wishbone 端口，外围 wrapper 负责把 Wishbone 请求转成芯片的地址、使能、写掩码等控制，再按宏延迟返回 ACK。功能仿真能验证数据路径，器件映射、时序和物理特性还需对应工具与模型检查。

### LiteX 的 Builder 生成了地址图，是否就说明 CPU 跑通了？

没有。`csr.csv` / `csr.json` 证明 LiteX 构造了哪些区域和寄存器地址；它们不证明 CPU 已取指或完成访问。第 06 章先比较生成地图与固件使用的地址，再运行 CPU，并要求完成端点收到预期写入。地图和运行时标志分别回答“构造对不对”和“程序有没有跑到”。

### 第 06 章那些 Python 辅助函数是什么？

`tour_paths.add_litex_to_path` 只定位 LiteX 源码并设置导入路径，不安装依赖。`build_program` 调 RISC-V GCC 和 `objcopy` 构建软件；`write_rom_init` 检查容量、补齐 ROM 镜像；`ProjectSoC` 描述 LiteX SoC；`build_and_run` 串起 Builder、地图检查、仿真编译和运行日志检查；`check_generated_map` 将 Builder 输出与固件地址约定比较。除 LiteX 的 `Builder` 外，这些都是本项目的 Python 脚本，不是 LiteX API。

## 阅读入口

每章 README 都可以独立阅读，包含实验问题、连接图或信号路径、运行命令、日志/波形位置，以及 PASS 能证明的范围。建议从 [00 环境](chapters/00-environment/README_zh.md) 开始；完整阶段计划见 [PLAN.md](PLAN.md)。
