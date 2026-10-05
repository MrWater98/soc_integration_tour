# 第 11 章：SPI 与 I²C 的每一位是谁送的

前面 UART 用一根 TX 线按时间发送字节。本章面对有地址或片选的设备：CPU 不应在读寄存器时凭空得到“预期值”，必须把命令送到引脚，等**从设备模型**响应，再读回来。为了看清边沿，主设备先用 CPU 对 CSR 的读写逐位驱动 SPI 和 I²C；这一章重点是协议，不引入另一个控制器的 FIFO 或 DMA。

## 输入与概念

本章自己的 `soc.py` 定义 CSR 引脚与 SPI 模型，`i2c_device.v` 是独立的 I²C 从设备；`main.c` 通过 CSR 逐位发起交易；`run.py` 生成固件并仿真。`startup.S`、`linker.ld` 提供前两章已学过的裸机启动与内存布局。运行所需的 LiteX、Verilator 和 RISC-V 工具链与第 00 章相同。

| 名词 | 本章的意思 | 观察点 |
| --- | --- | --- |
| SPI 片选 `CS_N` | 低电平才选中从设备 | 错误片选不产生 `SPI_FRAME` |
| SCLK / MOSI / MISO | 主机时钟 / 主机数据 / 从机数据 | `spi` 模块的波形与 `SPI_FRAME` |
| SPI 模式 0 | 空闲时钟低，主从双方在上升沿采样 | `spi_byte()` 每位先设 MOSI，再拉高 SCLK |
| I²C SCL / SDA | 时钟 / 双向数据线 | `i2c` 波形；SDA 高电平靠释放后的上拉 |
| 开漏 | 设备只能拉低 SDA，发 1 时放开让上拉拉高 | `sda = master_release & device_release` |
| START / STOP | SCL 高时 SDA 分别下降 / 上升 | `I2C_START`、`I2C_STOP` |
| ACK / NACK | 第 9 位时接收方拉低 SDA / 保持释放 | 地址 `0x86` NACK，正确地址 ACK |
| 重复 START | 不先 STOP，再次以 START 发送读地址 | 选寄存器后读回 `0x5a`、`0xc3` |

```text
SPI: CPU → spi_out CSR → CLK/MOSI/CS_N → 从设备命令译码
                                      从设备 MISO → spi_input CSR → CPU

I²C: CPU → i2c_out CSR → SCL、SDA 释放/拉低 → 0x42 从设备
                                     从设备 SDA 拉低/释放 → i2c_input CSR → CPU
```

## 这套 bit-bang SoC 用了哪些 LiteX 配置？

`SoCCore` 提供 CPU、复位地址为 0 的 ROM、4 KiB 片上 SRAM 和给裸机 C 程序使用的 16 KiB main RAM；默认 UART、Timer 和控制器都关闭。本章的 SPI/I²C 是小型 `AutoCSR` 模块，不是硬件控制器：`CSRStorage` 驱动输出引脚，`CSRStatus` 采样输入引脚，C 程序逐次写 CSR 形成协议边沿。完成寄存器则是位于 `0x80000000` 的独立、不可缓存 Wishbone 区域。

CSR 位宽和复位值直接定义协议初态：SPI 的 3 位输出复位为 `4`，让低有效 `CS_N` 保持高；I²C 的 2 位输出复位为 `3`，释放 SCL 和 SDA。改动复位值可能导致启动时 SPI 从设备被选中，或 I²C 线路在 START 前被拉低。增加或改名 CSR bank 会改变生成地址，所以运行器重新生成头文件，并用它编译 C 固件。这种引脚级方式刻意保持简单但速度慢；换成 LiteX 控制器后，CSR 接口会不同，协议时序也由硬件而非软件产生。

CSR 地址由本章 LiteX Builder 生成：`i2c_out=0xf0000000`、`i2c_input=0xf0000004`、`spi_out=0xf0001000`、`spi_input=0xf0001004`。`run.py` 在编译固件前和完整构建后都检查这些值。这里的 `spi_input` / `i2c_input` 是**当前引脚状态**，不是一个会自动执行协议的专用主控制器。

## SPI：16 个时钟组成一笔交易

CPU 先让 `CS_N=0`，发送 8 位命令 `0x9f`，再发 8 个空位给从设备回传数据。模型只在片选有效时采样 MOSI 上升沿；识别命令后，在后 8 个时钟上送出 `0xa5`。CPU 每个上升沿读取 MISO，并在第 16 位后让片选回高。日志因此有 `SPI_FRAME command=0x9f bits=16` 与 `PROTOCOL_PROBE value=0x000011a5`。

负例先保持 `CS_N=1` 做同样动作：MISO 的默认高电平读成 `0xff`，但模型**不记录有效 SPI 帧**。这说明“CPU 已经翻动时钟”不等于“从设备已被选中”。预测：若把正确交易的片选也保持高电平，完成码应是 `0x5a` 还是失败码？

## I²C：谁来拉低第九位

本章设备的 **7 位地址**是 `0x42`；在线上传输的写地址字节是 `0x84`，读地址字节是 `0x85`（最低位分别为 0 和 1）。CPU 先发送错误地址字节 `0x86`，模型保持 SDA 释放，CPU 读到 NACK。正确写交易的顺序是：

```text
START → 0x84 → ACK → 寄存器号 → ACK → 数据 → ACK → STOP
```

CPU 分别把寄存器 0 写为 `0x5a`、寄存器 1 写为 `0xc3`。读回时先用写地址选择寄存器，再发**重复 START**和读地址 `0x85`，设备开始逐位驱动 SDA。CPU 收到 8 位后在第九位**释放 SDA 表示 NACK**，告诉从设备本次只读一个字节，随后 STOP。模型记录两次 `I2C_MASTER_NACK value=1`；CPU 最后把 `0x5a` 与 `0xc3` 写进测试探针。

注意“释放 SDA”不是主动输出高电平；主机和从机的 release 都为 1 时，上拉才让线为高。开发时曾把从机发送位取反，设备日志仍说“准备发送 0x5a”，CPU 却实际读到 `0xa5`。错误被 CPU 的读回比较抓住，修正为 `release_sda=data_bit` 后通过。这是为什么要把软件比较和引脚协议模型一起检查。

## 运行与验收

```sh
python3 chapters/11-spi-i2c/run.py
```

正常日志中可以找到：

```text
SPI_FRAME command=0x9f bits=16
I2C_ADDRESS byte=0x86 ack=0
I2C_WRITE index=0 data=0x5a
I2C_READ index=0 data=0x5a
I2C_MASTER_NACK value=1
PROTOCOL_PROBE value=0x0012c35a
SOC_COMPLETE data=0x0000005a
```

脚本要求正确片选恰好一帧、错误地址 NACK、两个寄存器写读均由模型记录、两次读末尾 NACK，并且 CPU 最终成功。CPU 用 CSR 写操作形成协议时序；仿真进程有超时。证据在 `results/11/run.log`、`builder/csr.csv`、`builder/gateware/sim.vcd` 和 `firmware/program.map`。在波形中找 SPI SCLK 上升沿前 MOSI 是否稳定，再找 I²C SCL 高时的 SDA 下降/上升和第九位。日志是便捷索引，波形才保留每个边沿。

## 常见问题

### 这里用的是 LiteX 的 SPI/I²C 控制器吗？

不是。本章用本地 CSR 控制线脚，由 CPU 软件逐位生成 SPI 和 I²C 时序。这样每个边沿、片选和应答位都能从 C 代码追到波形。它适合学习协议与验证模型，不代表性能更高，也不替代 LiteX 或 FPGA 上的专用控制器。

### 为什么 SPI 错误片选时仍能读到 `0xff`？

从设备没被选中时，MISO 保持空闲高电平，CPU 读到的 8 位自然是 `0xff`。关键证据是模型没有记录有效帧，而不是把这个空闲值当成 Flash/器件响应。正常帧还必须有正确 `CS_N`、命令和时钟数。

### I²C 的 SDA 为什么不能由主机直接输出高？

I²C 是开漏结构：主机或从机只能拉低 SDA，想发 1 就释放线路，让上拉电阻把线拉高。若一端拉低、另一端硬推高，会形成电气冲突。仿真模型用双方 release 信号的组合表达“任意一方拉低，线路就是低”。

### ACK 和 NACK 是谁发的？

发送一个字节后，接收方控制第九个时钟的 SDA。接收方拉低表示 ACK，释放表示 NACK。写地址和数据后的 ACK 来自从设备；本章读完最后一个字节后，CPU 主机释放 SDA 发 NACK，表示不再请求更多字节。

## 本章速记

1. SPI 用片选决定哪个设备响应，模式 0 在时钟上升沿采样。
2. I²C 地址字节含 7 位设备地址和读写位；第九位由接收方 ACK 或 NACK。
3. I²C SDA 高来自上拉，设备只负责拉低或释放。
4. CPU 的数据比较与独立从设备的协议记录必须一致。
