# 从头设计验证 SoC

这个项目用 LiteX 和一颗 VexiiRiscv，从最小硬件开始搭一套能运行固件的 SoC。章节按集成过程逐步展开：先验证 CPU 取指，再加入总线、ROM、RAM 和地址图，随后用 LiteX 构造 SoC，并接入常见外设与外部存储器。

## 从最小系统逐步集成

Litex、HeteroSoC 或 Chipyard 都能快速拼出能运行的系统。我更想知道每个部件的最小构造和最小验证是什么：CPU 参数怎样选，总线请求由谁回答，汇编怎样变成 ROM 镜像，一个软件地址怎样到达目标设备。把这些边界拆开后，失败时能知道自己在查 CPU、固件、总线，还是地址图。

实验会留下地址表、编译产物、逐周期日志和波形。构建成功只说明硬件描述能生成；CPU 完成一次写入或协议检查器读回正确值，才是运行证据。负例也要有明确预期：例如没有 ACK 应该超时，未映射地址应该触发访问异常。

## 章节进度与运行入口

从仓库根目录运行。生成文件统一写到被 Git 忽略的 `results/` 下。

| 章 | 实验内容 | 运行命令 |
| --- | --- | --- |
| 00 环境 | CPU、固件和仿真器工具链 | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU 启动 | 复位、取指和指定写入 | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | 请求应答时序与失效场景 | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | 汇编生成镜像与复位映射 | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | 字节通道、栈帧和函数返回 | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 地址图 | 地址区域、重叠和未映射访问 | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`、`Builder` 和 AXI-Lite/Wishbone 集成 | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |
| 07 裸机 C | 启动代码初始化 `.data` 和 `.bss` | `PYTHONHASHSEED=0 python3 chapters/07-bare-metal/run.py` |
| 08 GPIO | 通过 CSR 控制和读取 GPIO | `PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py` |
| 09 UART | UART FIFO 与 8N1 引脚波形 | `PYTHONHASHSEED=0 python3 chapters/09-uart/run.py` |
| 10 定时器中断 | Timer 事件、PLIC 和 ISR 返回 | `PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py` |
| 11 SPI / I2C | 软件逐位生成协议和 NACK 检查 | `PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py` |
| 12 外部存储器 | 并行 SRAM、SDRAM 和 SPI Flash 访问路径 | `LITEDRAM_ROOT="$PWD/external/litedram" PYTHONHASHSEED=0 python3 chapters/12-memory/run.py` |

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

## 阅读入口

每章 README 都可以独立阅读，包含实验说明、连接图或信号路径、运行命令、日志/波形位置，以及 PASS 能证明的范围。建议从 [00 环境](chapters/00-environment/README_zh.md) 开始；完整阶段计划见 [PLAN.md](PLAN.md)。
