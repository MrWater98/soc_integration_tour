# 16：把 `.fs` 下载到板子，看见 CPU 真正运行

14 章描述电路并编译程序，15 章生成 `tutorial14.fs`。现在要把它交给 Tang Primer 20K，让板上的 FPGA 实现这套电路。

本章有两个连续的实验层次：**先用简单 LED 电路确认下载通路，再用 VexRiscv SoC 验证 CPU、串口、按键和复位。** 我们已经实际完成了固定 LED 图案和 SoC 上板；下面解释怎样做到，以及每一步说明什么。

## 1. 电脑与 FPGA 之间有两条用途不同的通路

我们连接 Dock 上标注 **USB-JTAG/UART** 的接口。本次板子通过 USB 枚举为 `0403:6010`，下载器提供 JTAG 与串口两个通道。

```text
电脑 / WSL
    │ 一根能传数据的 USB 线
    ▼
Dock 上的 USB-JTAG/UART 电路
    │
    ├─ JTAG 通道
    │     ▼
    │   FPGA 自带的配置入口
    │     ▼
    │   配置 SRAM ← 装入 .fs
    │     ▼
    │   FPGA 内部实现 CPU、ROM、总线、外设
    │
    └─ UART 通道
          ⇅
        FPGA 的 serial_rx / serial_tx 引脚
          ⇅
        我们生成的 UART 外设
          ⇅
        CPU 通过寄存器收发字符
```

- **JTAG 下载**负责把电路配置送进去。
- **UART**让已经运行的 CPU 与电脑收发字符。

下载成功与收到 `HELLO` 是两件事：前者说明配置传输完成，后者说明 CPU 执行到了打印代码。

这里使用 FPGA 自带的配置 JTAG。它与 13A 自己实现的教学 TAP 不同；本章也没有通过 GDB/OpenOCD 调试 CPU。

## 2. WSL 为什么可能看不见板子？

USB 插到 Windows 电脑后，设备先由 Windows 管理。WSL 能访问 Windows 文件，并不意味着 Linux 里的下载工具自动能访问这个 USB 设备。

```text
Windows 看见板卡
    │ usbipd 共享并附加设备
    ▼
WSL 看见 USB 设备
    │ openFPGALoader / 串口驱动
    ▼
下载 FPGA / 读取 UART
```

这一步只解决“工具能接触到硬件”，还没有给 FPGA 下载电路。

### Windows 端：将设备交给 WSL

若还未安装 usbipd-win，在 PowerShell 中安装：

```powershell
winget install --interactive --exact dorssel.usbipd-win
```

保持 WSL 运行，执行：

```powershell
usbipd list
```

找出板子对应的行。可以用插拔前后的设备变化确认，BUSID 以自己电脑列出的为准。

**管理员 PowerShell** 中共享一次：

```powershell
usbipd bind --busid 实际BUSID
```

随后附加到 WSL：

```powershell
usbipd attach --wsl --busid 实际BUSID
```

我们这次设备曾位于 `2-4`，状态变为 `Attached` 后，WSL 才能实际访问它。这个编号由电脑分配，换 USB 口或重新枚举后可能变化。[WSL USB 官方说明](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)

### WSL 端：确认 USB 与串口

```bash
lsusb
ls -l /dev/serial/by-id/
python -m serial.tools.list_ports -v
```

本次实际使用的 UART 路径为：

```text
/dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0
```

它在这台机器上对应 `ttyUSB1`；另一个接口用于 JTAG。`ttyUSB0/1` 是电脑分配的设备名，不能照抄到所有环境。优先使用自己机器实际出现的 `by-id` 路径。

## 3. 第一个实验为什么先用固定 LED 图案？

LED 图案只需要几根输出线，可以先回答：下载器能不能工作？管脚约束对不对？灯是不是低有效？

```text
电脑构建 LED 电路 → 得到 leds.fs → JTAG 下载
                                      │
                                      ▼
                              FPGA 输出固定电平
                                      │
                                      ▼
                                  LED 图案
```

这个电路没有 CPU，也不执行 C。看到灯亮，证明的是这条简单输出路径。

本章保留了独立示例：

```bash
source chapters/15-fpga-build/tools.sh
python chapters/16-board-smoke/build_examples.py --example leds
openFPGALoader -b tangprimer20k results/16-leds/leds.fs
```

查看 `examples/leds/` 中的 RTL 与约束，就能把每个输出位对应到管脚。这个示例的 LED 低有效，所以 0 表示亮；改固定图案之后，需要重新构建并下载才能看到变化。

`--example clock` 则加入 27 MHz 输入与计数器，生成 `results/16-clock/clock.fs`，让灯随时间变化。它进一步检查时钟路径，但仍没有 CPU。

这两个示例来源和版本记录在 `examples/UPSTREAM.json`。更细的 LED 修改过程见 [第一板实验](FIRST_BOARD.md)；理解完整 SoC 时继续下面的步骤。

## 4. 下载 SoC 前，先确认 JTAG 能识别 FPGA

连接核心板与 Dock，使用 USB-JTAG/UART 接口，并按官方图示把核心板使能开关置于使能位置。板上的电源灯亮只说明部分供电/指示路径有活动，不说明已经运行我们的固件。[板卡说明](https://wiki.sipeed.com/hardware/zh/tang/tang-primer-20k/primer-20k.html)

在教程根目录执行：

```bash
source chapters/15-fpga-build/tools.sh
python chapters/16-board-smoke/run.py --detect
```

脚本调用 `openFPGALoader -b tangprimer20k --detect`，将结果写入 `results/16-tang20k/detect.log`。

我们这次得到的识别包括：

```text
idcode 0x81b
manufacturer Gowin
model GW2A(R)-18(C)
```

这是下载工具对实际 JTAG 链上器件的识别；它还没有检查 CPU 程序。

## 5. 下载 SoC，同时收串口

使用 15 章默认 27 MHz 的结果：

```bash
python chapters/16-board-smoke/run.py --load-sram \
  --bitstream results/15-tang20k-build/tutorial14.fs \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0 \
  --seconds 20
```

串口路径必须换成自己机器实际出现的路径。当前固件使用 **115200 baud、8 数据位、无校验、1 停止位**，也写成 115200 8N1。波特率是收发双方约定的速度，修改 14 章 `--baud` 后，这里要传入相同的 `--baud`。

### `run.py` 具体按什么顺序做？

```text
① 打开 UART，准备接收
② JTAG 检测 FPGA，保存识别日志
③ 读取 .fs，记录文件 SHA256
④ openFPGALoader 将 .fs 下载到 FPGA 配置 SRAM
⑤ 持续读取 UART，保存收到的原始字节和文本
⑥ 检查是否出现固件的 HELLO 或 ALIVE 标记
```

为什么先打开串口？下载完成后 CPU 就可能开始打印；先准备接收，减少错过启动输出的机会。

命令只加 `--detect` 时只识别；只提供 `--serial` 时只采集已有设计的输出；不加任何硬件操作参数时，脚本只记录 SKIP 并展示下载命令。

### “下载到 SRAM”是什么意思？

这里的 SRAM 是 **FPGA 的配置存储**，保存 LUT 功能、线路连接等配置。

```text
FPGA 配置 SRAM：决定 FPGA 成为什么电路
SoC 的 SRAM/main RAM：电路里的存储器，供 CPU 存数据和栈
```

它们名字都带 RAM，但用途不同。本章下载配置 SRAM，不写板上的 Flash。断电后本次配置消失；重新上电可能加载 Flash 中原有设计，因此再次使用我们的 `.fs` 需要重新下载。

## 6. 从下载完成到 `HELLO`，内部发生了什么？

```text
.fs 装入 FPGA
    │
    ▼
CPU / ROM / RAM / UART / GPIO / CRG 电路建立
    │ ROM 已带本次程序初值
    ▼
上电等待结束 → PLL 锁定 → 系统复位释放
    ▼
CPU 从地址 0 取指，执行 _start
    ├─ 设置 SP
    ├─ 从 ROM 搬运 .data 到 RAM
    └─ 清零 .bss
    ▼
进入 main()
    ▼
uart_rxtx_write() → UART 外设 → serial_tx 引脚
    ▼
Dock 的 USB-UART → USB → WSL 串口
    ▼
电脑看到 14 HELLO
```

电脑没有把 C 程序“直接运行在 FPGA 上”。程序先被编译成 RISC-V 指令并放进 ROM；FPGA 中的 VexRiscv 再逐条取指执行。

## 7. 灯、串口和按键各应该怎样表现？

本次实物已收到：

```text
14 HELLO: CPU reached main; LEDs are mapped
BUTTONS=0x00000000
14 ALIVE: Tang Primer 20K CPU polling
```

| 观察 | 电路怎样产生它 | 可以据此确认什么 |
|---|---|---|
| 心跳灯按约 1 Hz 亮灭 | 系统时钟驱动计数器 | 时钟、复位、计数器和该输出路径在运行 |
| `HELLO` | CPU 进入 `main()`，写 UART | CPU 已执行到这段固件，串口发送路径可用 |
| 持续 `ALIVE` | 固件每一百万次循环打印 | CPU 持续执行轮询循环 |
| S1 按下出现 `BUTTONS=...1`，松开为 0 | 输入同步器 → CSR → CPU 读取 | 按键读取路径可用 |
| CPU LED 跟随 S1 | CPU 根据读到的值写 LED CSR | 读取、固件处理、输出这条路径可用 |
| S0 松开后再次出现 `HELLO` | 按键触发 CRG/系统复位，再执行 ROM | 这次实物复位与重启路径可用 |

本章 LiteX `led4` 是心跳，`led5` 是 CPU 输出。按本次实物对照，分别对应示例中的 LED1、LED0。不要把板上的任意常亮灯都认作这两个输出。

`ALIVE` 不是精确的一秒定时器。本次 27 MHz 的轮询输出间隔约 0.59 秒，54 MHz 约 0.30 秒；这是这份固件的观察结果，随程序变化而变化。

S1 的机械触点可能抖动，所以一次操作出现多行状态变化并不奇怪。本章固件反复读取状态，没有实现“一次按压只触发一次”的消抖逻辑。

## 8. 没有预期输出时，按链路排查

从最外层开始，每一步回答一个具体问题：

```text
WSL 看见 USB 吗？
    ↓
JTAG 能识别正确 FPGA 吗？
    ↓
指定 .fs 下载成功吗？
    ↓
心跳路径有活动吗？
    ↓
选对 UART 接口和波特率了吗？
    ↓
CPU 是否运行到 HELLO / ALIVE？
    ↓
S1、LED 和 S0 复位行为是否符合固件？
```

| 现象 | 优先检查 |
|---|---|
| Windows 有设备，WSL 没有 | usbipd 的 BUSID、附加状态、是否重新插拔 |
| WSL 有 USB，但识别失败 | 核心板使能、下载接口、USB 权限与 JTAG 通路 |
| 下载成功，两个目标灯都不活动 | 文件是否属于本板、引脚/READY-DONE 配置、时钟与复位 |
| 心跳正常，没有串口 | `if01` 等实际 UART 接口、波特率、固件和 CPU 路径 |
| 串口乱码 | 接收波特率是否匹配本次固件；是否混入旧接收缓冲数据 |
| 有 `ALIVE`，没有初始 `HELLO` | 可能错过启动，按 S0 重启再观察 |
| 按键不改变值 | 是否按 S1、T3 引脚、极性及读取路径 |

USB/驱动可能保留先前的串口数据；比较打印间隔时，先等待接收流稳定，再测新数据。看见一段旧文本，不能据此判断刚下载的版本已经启动。

## 9. 结果在哪里？怎样确认是哪份设计？

默认目录为 `results/16-tang20k/`：

| 文件 | 内容 |
|---|---|
| `detect.log` | JTAG 识别结果 |
| `load.log` | 下载工具输出 |
| `uart.bin` / `uart.txt` | 收到的原始字节与可读文本 |
| `summary.json` | 下载文件路径、SHA256、各步骤状态 |
| `REPORT.md` | 本次实物观察的汇总记录 |

14/15 章生成脚本里的上板 SKIP 表示该脚本没有执行实物验证；早期报告还保留了“板子未到”的文字。当前实物运行结论看本章下载日志、串口记录与 `REPORT.md`。

自动脚本检查下载和串口标记；灯、S1、S0 的行为还需要实际观察，因此脚本中的 `manual_checks` 默认保留待记录状态。本次用户已确认这些行为，汇总写在 `REPORT.md`。

54 MHz 已有另一份记录。选择配套文件、单独结果目录：

```bash
python chapters/16-board-smoke/run.py --load-sram \
  --bitstream results/15-tang20k-build-54mhz/tutorial14.fs \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0 \
  --seconds 20 --output results/16-tang20k-54mhz
```

## 本章结束时，已经证明了什么？

我们已用开源工具把单核 VexRiscv、片内存储、UART 和 GPIO 放到真实 Tang 板上，并观察到固件启动、持续输出、按键控灯和按键复位。27/54 MHz 都有实物运行记录。

这是基本上板验收。接下来 17 章把“看起来能跑”变成可计数的 RAM、中断、串口与热复位压力测试；DDR、Linux、Flash 固化各有自己的后续实验。
