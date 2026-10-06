# 从头设计验证 SoC

这个项目用 LiteX 和一颗 **VexRiscv**，从最小硬件开始逐步搭出能运行固件的 SoC。基线选择 LiteX 的 `vexriscv/minimal`：RV32I，没有指令缓存和数据缓存。CPU 的取指和数据接口都是 Wishbone，LiteX 把它们接到 SoC 的 Wishbone 互连上。

每一章只增加一个集成点，运行证据保存在 `results/<章节>/`：地址图、固件镜像、仿真日志、波形，以及仿真器实际编译的 RTL。硬件描述生成成功只证明“能构造”；CPU 写出完成码或协议检查器读回预期结果，才证明运行路径成立。

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

00–12 章有独立实验；13–15 章仍是集成回归和 FPGA 计划。完整阶段约定见 [PLAN.md](PLAN.md)。
