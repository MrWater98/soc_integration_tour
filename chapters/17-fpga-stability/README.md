# 17：让 FPGA 上的 SoC 持续工作，并知道自己验证了什么

第 16 章证明 SoC 能启动。本章让它持续做事：写读 RAM、处理中断、收发串口，再由电脑主动检查是否丢回复、停止进度或意外重启。

这里有两套程序同时运行：**FPGA 内的 RISC-V 固件**，以及**电脑上的 Python 检查器**。构建电路的 Python 程序是第三个角色，运行时间也不同。

## 1. 先看整个流程

```text
电脑，构建阶段                          FPGA 配置输入
build.py → LiteX 生成电路与接口
    └─ firmware_builder.py → GCC → ROM 初值
    └─ synthesize.py → Yosys 网表
    └─ route.py → nextpnr → Apicula ──→ tutorial17.fs

电脑，验收阶段                          Tang Primer 20K
run.py ── JTAG 下载 .fs ─────────────→ 配置 SRAM
   │                                     ↓
   │                              PLL / 系统复位
   │                                     ↓
   │                              CPU：_start → main
   │←─ BOOT：时钟配置、随机种子 ─────────┤
   │                                     ├─ RAM 模式/随机/字节写
   │                                     ├─ Timer → IRQ → ISR
   │                                     └─ 硬件 RAM 事务计数
   ├─ E + 随机编号 ── UART ─────────────→ 命令解析
   │←─ ECHO + 相同编号 ──────────────────┤
   │←─ PASS：轮数、IRQ、读写量 ───────────┤
   ├─ R ── UART ────────────────────────→ CSR 软件复位
   │←─ 新 BOOT、新阶段进度 ───────────────┤
   └─ 数值/顺序/超时检查 → summary.json
```

本章 CPU 是普通单核 `vexriscv standard`，使用片内 ROM/RAM。没有把板上 DDR 接进来。17A/17B 的 SMP 仿真和 17C 的 Linux 尝试分别有自己的目录和结论。

## 2. 本章源文件各自负责什么？

| 文件 | 角色与主要输入/输出 |
| --- | --- |
| [config.py](config.py) | 板卡与可调参数：时钟、容量、栈预算、上电等待等 |
| [build.py](build.py) | 构建入口；扩展 Config 加入测试字数、种子、故障开关；组织两遍生成 |
| [soc.py](soc.py) | SoCCore、CRG、软件复位控制器、RAM 事务观察器与外设连接 |
| [io_cores.py](io_cores.py) | 心跳计数器、输入同步和 LED 控制寄存器 |
| [timer.py](timer.py) | 本章明确命名的倒计数器及事件/IRQ 电路 |
| [firmware_builder.py](firmware_builder.py) | 生成链接脚本、测试头文件；调用 GCC/objcopy，返回 ROM 字数组 |
| [startup.S](startup.S) | 初始化 sp、数据区、中断入口；保存/恢复 ISR 使用的寄存器 |
| [main.c](main.c) | FPGA CPU 实际执行的压力程序和串口命令解析 |
| [synthesize.py](synthesize.py) | 用 Yosys 将完整 RTL 映射为 Gowin 单元 |
| [route.py](route.py) | 布局布线、时序目标检查、打包 bitstream |
| [gowin_primitives.v](gowin_primitives.v) | Icarus 展开检查所需原语；不是本章 PLL 的真实模拟模型 |
| [run.py](run.py) | 电脑上的串口检查器：识别/下载、发命令、读日志、计数、超时和汇总 |
| [campaign.json](campaign.json) | 多场景运行计划及人工测量记录字段 |
| [campaign.py](campaign.py) | 按计划依次调用主机检查器，汇总各场景结果 |

`build.py` 和 `run.py` 不会互相自动代替。前者可以在没有板卡时执行；后者需要真实串口，而且 `--load` 时还要访问 USB JTAG。

## 3. 参数在哪里设置？哪些数字不是固定规格？

`build.py` 的 Config 继承本章板卡 Config，并增加：

```python
@dataclass(frozen=True)
class Config(BoardConfig):
    stress_words: int = 512
    seed: int = 1
    inject_fault: bool = False
```

| 配置 | 当前默认 | 实际意义 |
| --- | --- | --- |
| 参考时钟 | 27 MHz | 当前板卡晶振输入事实 |
| 系统时钟 | 54 MHz | 本章 PLL 目标；可用 `--sys-clk-hz` 修改 |
| UART | 115200 baud | 固件 UART 与主机串口保持匹配 |
| ROM / SRAM / main RAM | 8 / 4 / 16 KiB | 当前容量选择，单位最终是字节 |
| 栈预算 | 1024 字节 | 链接脚本保留空间；不是硬件栈越界保护 |
| 压力数组 | 512 个 32 位字 | 2048 字节，只测试主 RAM 的一部分 |
| 随机种子 | 1 | 固定便于复现；`--seed` 可改 |
| 故障注入 | False | 负例构建才启用 |
| Timer reload | 系统频率 / 1000 | 约 1 kHz，具体倒计数有边界周期 |
| 进度报告间隔 | 100 轮 | 当前 C 固件里的选择，不是命令行参数 |
| UART 请求间隔 | 约 0.5 秒 | 当前主机检查器的选择 |
| 回显/启动/进度超时 | 3 / 5 / 5 秒 | 当前主机检查门槛，不是 UART 协议规定 |

`--stress-words` 当前接受 16–2048，非零 32 位种子由构建入口检查；这些是教程实验范围。扩大数组还需通过数据区和栈的布局检查，不能只看参数解析成功。

### 软件随机与主机随机不同

RAM 数据用固定种子的 xorshift32，改变种子需要重新编译固件。主机每次用 `secrets.token_hex(4)` 产生串口编号，默认不会保存一个可重放的随机生成器种子；实际发出/回显的编号可从日志追查。

## 4. 相比第 14 章，多接了哪些硬件？

```text
VexRiscv → Wishbone ─┬─ ROM：压力固件
                    ├─ SRAM
                    ├─ main RAM：数组、变量、栈
                    │        └─ RAMTraffic：观察完成传输
                    └─ CSR 桥 ─┬─ UART / LED / 按钮
                               ├─ timer0 → IRQ handler → CPU
                               ├─ ctrl.reset → 系统复位
                               └─ traffic.reads / writes
```

`soc.py` 仍设置 `with_timer=False, with_ctrl=False`，是关闭 SoCCore 的默认版本；随后显式添加本章 `TutorialTimer` 和 `ResetControl`。因此不能看到 False 就认定没有 Timer/软件复位电路。

`self.irq.add('timer0', ...)` 把 timer0 的事件中断接入 LiteX 的 IRQ 分配。当前生成表中 UART 是 IRQ 0，Timer 是 IRQ 1；固件引用 `TIMER0_INTERRUPT`，没有把 1 硬写成通用规则。

### 当前 CSR 地址表

依据 `results/17-counted/builder/csr.csv`：

| 寄存器 | 字节地址 | 用途 |
| --- | --- | --- |
| `uart_rxtx` | `0xf0000000` | 字符收发 |
| `leds_output` | `0xf0000800` | LED5 控制 |
| `buttons_input` | `0xf0001000` | 按钮1状态 |
| `timer0_load` / `reload` | `0xf0002000` / `0xf0002004` | 停用时装载值、周期重装值 |
| `timer0_en` | `0xf0002008` | 计数器使能 |
| `timer0_ev_pending` / `ev_enable` | `0xf0002018` / `0xf000201c` | 清事件、允许 Timer 事件中断 |
| `ctrl_reset` | `0xf0002800` | 软件系统复位请求 |
| `traffic_reads` / `writes` | `0xf0003000` / `0xf0003004` | 主 RAM 的硬件完成读/写计数 |

这些地址来自当前 bank 配置和 paging，不是 Tang 出厂固有的外设地址。生成 `csr.h` 提供同一张硬件表对应的 C 函数。

## 5. 构建阶段的文件怎样依次产生？

```text
配置 + 临时 ROM 指令
           ↓ generate(..., rtl=False)
Builder：csr.h、soc.h、mem.h、csr.csv
           ↓ firmware_builder.py
linker.ld + test_config.h + startup.S + main.c
           ↓ RISC-V GCC
program.elf + program.map + link.log
           ↓ objcopy
program.bin
           ↓ Python 按小端转字数组并在内存中填满 ROM
真实 rom_words
           ↓ generate(..., rtl=True)
Builder：tutorial17.v、存储初值、CST、构建脚本
           ↓ 本章收集、Icarus 展开检查
rtl/ + sources.json + files.f + elab.vvp + manifest.json
           ↓ --build 才继续
synthesize.py → synthesis/netlist.json
           ↓ route.py
build/routed.json + pnr-report.json + tutorial17.fs
```

CPU 的 `VexRiscv.v` 来自 CPU 数据包；不是 GCC 从 main.c 生成 CPU 电路。GCC 编译的是 CPU 运行的指令。

`elab.vvp` 是 Icarus 展开输出。本章只创建它，没有拿它运行完整 CPU 压力仿真；数字功能证据主要来自本章真实板卡运行。

## 6. `results/17-counted` 怎样读？

```text
results/17-counted/
├── manifest.json              配置、PLL、HDL 快照哈希
├── REPORT.md                  生成步骤的说明，不自动等于上板结论
├── freeze.json                本轮验收时整理的固定输入身份
├── elaborate.log / generate.log
├── builder/
│   ├── csr.csv / csr.json
│   ├── software/include/generated/  CSR/SoC/内存头文件
│   └── gateware/              原始顶层、初值、CST、构建命令
├── firmware/
│   ├── linker.ld / test_config.h
│   ├── program.elf / program.bin / program.map
│   ├── compile-command.json
│   └── link.log
├── rtl/
│   ├── tutorial17.v / VexRiscv.v
│   ├── tutorial17_rom.init
│   ├── tutorial17_sram.init / tutorial17_main_ram.init
│   ├── tutorial17_mem.init
│   ├── gowin_primitives.v
│   └── sources.json / files.f
├── constraints/tutorial14.cst
├── synthesis/
│   ├── rtl/                   综合使用的经哈希核对的副本
│   ├── synth.ys / synthesis.log / console.log
│   ├── netlist.json / netlist.v / netlist.edif
│   ├── stat.json / summary.json / REPORT.md
└── build/
    ├── netlist.json / tutorial14.cst
    ├── routed.json / pnr-report.json
    ├── tutorial17.fs
    ├── commands.json / nextpnr.log / pack.log
    └── summary.json / REPORT.md
```

许多工具工作文件留在本机、未纳入 Git。克隆后可能只看到已跟踪的完整 RTL、约束、清单和关键报告；需要临时产物时运行本章构建命令。

### 容易误解的文件名

- `constraints/tutorial14.cst` 沿用构建脚本的约束文件命名，是**本章**生成的 `tutorial17.cst` 的复制件；不是偷偷读取第 14 章另一套电路。
- `build/netlist.json` 是综合结果的副本，供 nextpnr 在自己的工作目录读取，不是再次执行 C 编译。
- `tutorial17_mem.init` 对应顶层的其他 Memory（当前 Identifier），不要把它按文件名当成 CPU 主 RAM。
- `synthesis/rtl/` 是综合输入副本，根目录 `rtl/` 是完整源快照；核对哈希可以追溯是否同一套输入。
- `freeze.json` 与 `17-acceptance` 是这次验收整理时写出的文件，不是每次 `build.py` 都自动输出的标准文件。

## 7. 固件启动：实际数据与栈落在哪里？

当前 `17-counted/firmware/program.map` 给出：

```text
ROM 的 .data 加载地址：0x00000710
RAM 的 .data：        0x40000000 .. 0x40000007
RAM 的 .bss：         0x40000008 .. 0x4000085b
预留栈下界：          0x40003c00
初始 sp：             0x40004000
```

这些是这一份 ELF 的链接结果。改变数组、编译器优化或代码后可能不同。`program.map` 中结束符号是区间末尾的下一地址。

`initialized=0x12345678` 与初始化随机状态需要从 ROM 拷贝到 RAM；数组、IRQ 计数等 `.bss` 对象由 `_start` 清零。主程序先检查 `initialized`、`zeroed`、`irq_count`，失败报告 code 4。

`startup.S` 设置 sp、mtvec 和 mie，再初始化数据。`trap_entry` 在进入 ISR 前分配 64 字节栈帧，保存 ra、临时寄存器、参数寄存器；调用 C 的 `isr()` 后恢复并 `mret`。

这里保存 ra 是因为 C ISR 本身可能调用函数；CPU 的异常返回位置由 `mepc` 等异常机制保存，不能把 ra 与异常返回 PC 混为一谈。栈预算检查只保证静态区未侵入保留区，不测最深运行时栈使用。

## 8. 每轮 RAM 测试到底执行什么？

`main.c` 的一轮：

```text
pattern(0)             → 全数组写、全数组读并比较
pattern(0xffffffff)     → 同上
pattern(0xaaaaaaaa)     → 同上
pattern(0x55555555)     → 同上
pattern(随机序列)        → 写入和预期值分别重新生成
bytes()                → 一个字的四次字节写与读回
rounds++               → 一整轮成功后才加一
service()              → 处理串口命令
GPIO 更新               → LED5 跟随按钮1
每 100 轮检查/报告 IRQ 和计数
```

默认每种模式遍历 512 个字，五种模式共有 2560 次数组字写与 2560 次校验读取；再加字节测试、栈和其他程序访问。这里算的是软件访问，不等于同样数量的外部 Wishbone 传输。

随机模式先写一个 xorshift32 序列，读阶段重新计算预期；比较的是数据，而不是仅对一个“通过标记”做检查。固定种子只覆盖一条确定序列；修改种子需新建独立构建目录。

字节测试：

```text
初始字             0x11223344
低到高四字节        44 33 22 11
分别写入            55 aa 66 bb
最终 32 位字         0xbb66aa55
```

这样同时检查当前小端布局和窄写效果。`ram` 是 volatile 数组，编译器必须实际执行访问；缓存仍可能参与，因此“实际访问”不表示每次都到块 RAM。

## 9. Timer 中断怎样维持进度？

`TutorialTimer` 用显式名称创建 load、reload、en、value 和事件寄存器。本章这样写便于稳定生成 C 接口，也让读者能看到最小计数/事件电路。

```text
en=0：count 装载 load
 en=1：count>0 时减一；count=0 时重装 reload
                        │
                        ▼
                  zero 事件 pending
                        │ ev_enable
                        ▼
                LiteX IRQ 分配 → CPU
                        ↓
                trap_entry → isr()
                        ↓
                清 timer0 pending，irq_count++
```

`reload=CONFIG_CLOCK_FREQUENCY/1000` 使频率约为 1 kHz；零值重装等周期使它不是精确的实验室频率源。

本固件还设置普通 VexRiscv 的每源中断掩码 CSR `0xbc0`，位由 `TIMER0_INTERRUPT` 指定。这是该 CPU 集成的机制，不是可移植到任意 RISC-V 核心的标准 CSR 地址。

ISR 要求 mcause 表示中断，且 Timer pending 有效，否则 fail(1)。每 100 轮主程序比较 `irq_count` 与上一报告值；不增长就 fail(5)。这检查中断仍在推进，但不保证每个硬件计时事件都一一对应：pending 在未处理时可能合并多个事件。

UART 事件中断关闭，收发靠轮询；Timer 中断仍开启，两者并不矛盾。

## 10. 硬件事务计数与软件轮数有什么区别？

`soc.py` 的 `RAMTraffic` 观察主 RAM 从设备：

```python
self.sync += If(bus.cyc & bus.stb & bus.ack,
    If(bus.we, writes.eq(writes + 1))
    .Else(reads.eq(reads + 1)))
```

计数器不发起事务、不修改应答。CPU 从 CSRStatus 读取结果，然后经 UART 报告。

| 计数 | 含义 |
| --- | --- |
| `rounds` | 完整通过的固件测试轮数 |
| `irq` | C ISR 已经处理并计数的 Timer 中断 |
| `reads` / `writes` | 主 RAM 从设备完成的 Wishbone 传输 |
| `echoes` | 主机收到并核对成功的请求编号 |

主 RAM 读写也包含栈/变量等访问，但不包含 ROM、CSR。缓存命中的 load 不会增加外部 RAM 读计数；当前核心的数据缓存策略也影响写传输。因此大量写、较少读不是“测试程序没读 RAM”，需要按采样位置解释。

32 位硬件计数器会回绕；主机在同一启动阶段用模 2³² 差值累加，前提是相邻样本之间不会绕完整一圈。系统复位清零后建立新阶段，不把清零误认为一次巨大回绕。

## 11. UART 协议：固件与主机交换什么？

| 方向 | 内容 | 用途 |
| --- | --- | --- |
| 固件 → 主机 | `17 BOOT hz=... seed=...` | 开始新启动阶段，核对固件参数 |
| 主机 → 固件 | `E` + 8 个十六进制字符 + 换行 | 请求随机编号回显 |
| 固件 → 主机 | `17 ECHO ` + 编号 | 主机核对内容和唯一性 |
| 主机 → 固件 | `R` + 换行 | 请求软件热复位 |
| 固件 → 主机 | `17 RESET` | 固件接受请求，准备执行复位 |
| 固件 → 主机 | `17 PASS rounds=... irq=... errors=... reads=... writes=...` | 进度报告，值为十六进制 |
| 固件 → 主机 | `17 FAIL code=...` | 固件捕获具体错误 |

`service()` 在一轮结束后执行，不是每个字符立即中断 CPU。RAM 操作期间 UART FIFO 仍在接收；主机低速发送编号，避免这个示例靠超量字符淹没 FIFO。

固件命令缓冲区当前 64 字节。固件回显 E 后面的文本；严格的编号检查主要由主机完成，它不是完整的命令格式校验器。

### 曾经抓到的 RX FIFO 问题

第一次 BOOT 后出现 code 3，命令缓冲区溢出。主机只发十个字符，原因却是程序反复读取队首字符：

```text
RX FIFO：[E][1][2]...
          ↑ 读取 rxtx 得到 E，默认模式尚未弹出
清 RX pending（掩码 2）→ 队首前进到 1
```

修正是读取后执行 `uart_ev_pending_write(2)`。这里 2 是当前 RX 事件位 1 的掩码，属于这个 UART 配置；`uart_ev_enable_write(0)` 只关闭 IRQ，不负责消费字符。

## 12. 软件复位为什么需要特别设计？

固件收到 R 后先打印 RESET，等待 `uart_txempty` 条件，再写 `ctrl_reset_write(1)`。这个等待是当前驱动使用的队列状态条件，不应推导为任何 UART 实现都保证最后一个停止位已经发完。

```text
CPU store ctrl_reset
          ↓ ResetControl 的写脉冲/保存位组合
        soc_rst
          ↓ LiteX 的 SoC reset 连接逻辑
        crg.rst
          ↓ 系统复位同步器
CPU、外设、计数器进入复位，PLL 继续供时钟
          ↓ 请求消失，系统同步退出复位
_start 再次执行 → 新 BOOT → 新一轮测试
```

`ResetControl` 的 `soc_rst = reset.re & reset.storage` 利用寄存器写事件，不是从 Python 调用一个 CPU 重启函数。原生 SoC 的 reset 连接逻辑把兼容的 `ctrl.soc_rst` 接到 CRG 请求。

早期实现把软件请求也送到 PLL reset，出现 RESET 后没有 BOOT：系统时钟停止，依赖该时钟的逻辑无法撤销请求。现在只有上电/外部按钮负责 PLL reset，软件请求进入系统域同步器。

## 13. 主机 `run.py` 如何判定通过？

### 下载前后

1. 读输入目录的 `manifest.json`，取得时钟、UART、种子等配置。
2. 先打开串口，关闭 DTR/RTS 自动状态，清主机接收缓冲，避免错过下载后的早期 BOOT。
3. `--load` 时用 openFPGALoader 探测，要求识别到预期 FPGA。
4. 从 `build/summary.json` 取 bitstream 哈希，对当前 `.fs` 实际求哈希核对。
5. SRAM 下载；本命令没有 Flash 写入步骤。
6. 开始计时、接收数据、按换行拼出完整记录。

### 运行中的状态

`pending` 保存“已经发出、尚未收到回复”的编号。回复只有在字典中存在才算成功；重复/未知编号失败，等待超过 3 秒失败。

BOOT 建立一个 `epoch`。主机核对频率/种子，非计划 BOOT 会被判为意外重启；5 秒内没收到初始 BOOT、后续没进度或请求复位后没 BOOT，也判失败。

下载前旧程序的数据可能残留，实际日志开头可能有半行。主机在观察到 BOOT 前不计正常进度；BOOT 行本身可以通过正则在混合行中定位。并非 `uart.log` 第一行必定是新固件 BOOT。

### 最后检查的门槛

正常场景要求：最大轮数至少 `--min-rounds`、最大 IRQ 至少 `--min-irqs`、至少 3 个回显、完成指定热复位次数、启动次数为复位数加一，以及存在非零 RAM 硬件读写计数。

这些最大值门槛不是“每个 epoch 都至少做同样次数”的断言。结束时还记录 `pending_echoes_at_end`；当前最终断言没有强制它为 0，本轮实测它为 0。接近结束才发出的请求可能未达到超时期限，解释其他结果时应一起看这个字段。

当前检查器依赖有初始 BOOT 的运行流程，推荐 `--load`。只附着一份已运行很久、没有新 BOOT 的程序，可能触发启动超时。

## 14. 读一条真实日志，别把十六进制当十进制

`17-counted-hardware/uart.log` 的最后一次进度：

```text
599.986239 17 PASS rounds=0005EC68 irq=00092794 errors=00000000 reads=00023018 writes=3C01943F
```

| 字段 | 解码结果 |
| --- | ---: |
| 行首主机时间 | 本次计时窗口约 599.986 秒，非 FPGA 精确时间戳 |
| rounds | 388200 轮 |
| irq | 599956 次 ISR 计数 |
| errors | 0 |
| reads | 143384 次完成读 |
| writes | 1006736447 次完成写 |

`17 PASS` 是固件阶段性进度，主机还要完成整个窗口的协议、启动和超时检查才能给场景 PASS。

### 热复位日志怎样读？

```text
5.516899 17 RESET
5.516899 17 BOOT hz=0337F980 seed=00000001
```

`0337F980` 是十六进制的 54000000。两行可能在同一串口读取批次到达，因此使用同一个主机时间戳；不能说硬件复位耗时精确为零。

## 15. summary.json 中每个统计量是什么意思？

| 字段 | 来源与含义 |
| --- | --- |
| `status` / `error` | 主机检查器结论及失败原因 |
| `parameters` | 本次主机命令参数，不是全部硬件构造参数 |
| `clock_hz` | 从 manifest 读的配置，并与 BOOT 核对；非仪器测频 |
| `bitstream_sha256` | `--load` 时验证的实际配置文件身份 |
| `boots` | 观察到的 BOOT 次数 |
| `warm_resets` | 已发请求且观察到新 BOOT 的软件复位次数 |
| `echoes` | 成功匹配并消费的随机编号回复 |
| `max_rounds` / `max_irqs` | 各启动阶段中最大的一个报告值 |
| `epochs` | 每阶段的启动时间、最新轮数/IRQ、累计读写 |
| `total_*_lower_bound` | 各阶段累计到最后进度报告的数量下界 |
| `elapsed_seconds` | 下载结束后主机检查循环的窗口，可能略超请求时长 |
| `longest_observed_epoch_seconds` | 最大 BOOT 至下一 BOOT/窗口末尾间隔，含主机接收粒度影响 |
| `pending_echoes_at_end` | 结束时尚未匹配的请求数 |
| `fault_caught` | 是否捕获固件 FAIL；在负例里是预期行为 |
| `ambient_c` / `supply_v` / `measurement_note` | 人工提供的测量记录；脚本不控制电源也不测温 |
| `cold_boot` / `temperature_voltage` | 未执行的物理检查或单点记录状态 |

累计值叫下界，因为最后一次报告到结束之间仍会执行操作；热复位前未报告的尾部操作也可能遗漏。读写计数由固件依次读取，不是同一时钟的原子快照。

`REPORT.md` 是 summary 的人读摘要。构建目录、硬件运行目录、综合目录各有同名文件，必须结合所在目录理解。

## 16. 为什么有这么多 results/17* 目录？

| 目录 | 属于哪一步，怎样使用 |
| --- | --- |
| `17` | 早期普通单核构建快照，尚未包含后来的 RAM 硬件观察器 |
| `17-hardware` | 早期 180.03 秒窗口、3 次热复位、356 回显的历史证据 |
| `17-counted` | 54 MHz、含硬件 RAM 读写计数的构建输入与 bitstream |
| `17-counted-hardware` | 上述电路的 600.04 秒不复位连续实测 |
| `17-counted-resets` | 同一 54 MHz 电路的独立 60.01 秒、10 次热复位实测 |
| `17-counted-27mhz` | 相同测试思路的 27 MHz 独立构建 |
| `17-counted-27mhz-hardware` | 27 MHz 连续 120.02 秒实测 |
| `17-fault` / `17-fault-hardware` | 故意翻转 RAM 位的构建与真实捕获结果 |
| `17-host-check` | 早期主机检查器修改后的短回归，不是新长时间验收 |
| `17-restored54` | 多频率实验后恢复 54 MHz 版本的短检查 |
| `17-acceptance` | 本轮已执行案例与冻结身份的整理汇总，不是另一个 FPGA 电路 |
| `17a*` | SMP 一个 hart 的真实 RTL 仿真，属于 17A |
| `17b*` | SMP 两个 hart 的正常、延迟、错误/不响应实验，属于 17B |
| `17c-linux` | 上游 Linux 目标的输入生成尝试和失败记录，无 Linux 启动结果 |

旧报告没有 `reads/writes/epochs` 等新字段很正常，不能给历史报告补上未测量的值。当前主机正例要求硬件读写计数，所以要使用当前生成版本，不应拿旧 `17` bitstream 直接跑新检查器。

早期 180 秒窗口里有复位，所以不是 180 秒不间断运行。它的最大轮数 29600、最大 IRQ 44947 也不是四次启动阶段的累计值。

## 17. 故障注入怎样证明校验器确实抓错？

`--inject-fault` 编译时生成 `INJECT_FAULT=1`。当前代码在 `rounds==3` 时，于写入与读回之间翻转 `ram[STRESS_WORDS/2]` 的一位，默认下标 256。

```text
第 4 轮开始 → 正常写入数组
                   ↓ 故意 xor 1
                 ram[256] 错误
                   ↓ 读回与预期比较
          fail(0x10000000 | 256)
                   ↓ UART
          17 FAIL code=10000100
                   ↓ 主机 --expect-fault
核对精确错误码 → PASS: injected RAM error captured
```

这是预期失败被正确捕获的 PASS，不是这份故障固件运行正常。该运行很早结束，不能给它要求完整 60 秒或若干次回显；`seconds` 是最大窗口而非负例必须坚持的时长。

| 错误码 | 当前 C 实现对应的问题 |
| --- | --- |
| 1 | 进入 ISR 时中断/Timer pending 条件不符合 |
| 2 | 字节写读回不符合 `0xbb66aa55` |
| 3 | UART 命令缓冲区溢出 |
| 4 | `.data/.bss` 启动检查失败 |
| 5 | 报告间隔内 IRQ 计数不增长 |
| `0x10000000 | i` | RAM 校验失败，下标 i |

其他协议/哈希/超时错误由 Python 抛出并写入 summary 的 `error`，不一定存在一个固件 FAIL 码。

## 18. 怎么重现，怎么选择输出目录？

从仓库根目录运行。板卡 USB JTAG/串口应先附加到 WSL。

```bash
# 当前 54 MHz 版本；新目录避免覆盖已验收历史快照
python chapters/17-fpga-stability/build.py --build --output results/17-new

# 连续运行不夹杂热复位
python chapters/17-fpga-stability/run.py --load --input results/17-new \
  --output results/17-new-continuous --seconds 600 --warm-resets 0 \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0

# 同一份输入，单独测试热复位
python chapters/17-fpga-stability/run.py --load --input results/17-new \
  --output results/17-new-resets --seconds 60 --warm-resets 10 \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0
```

`--input` 是电路/固件构建目录；`--output` 是主机观察结果。输入目录中的 manifest 与 build summary/.fs 必须配套。Git 不保存所有中间网表和 bitstream，缺文件时需先重建。

仅运行 `build.py` 而不带 `--build` 会交付 RTL/固件/展开结果，没有生成可下载 `.fs`。不要因为输出目录中残留以前的文件就把它当作本次工具已执行。

### 频率、种子、故障分别建立独立版本

```bash
python chapters/17-fpga-stability/build.py --build --sys-clk-hz 27000000 \
  --seed 7 --stress-words 1024 --output results/17-new-27mhz

python chapters/17-fpga-stability/build.py --build --inject-fault \
  --output results/17-new-fault
python chapters/17-fpga-stability/run.py --load --expect-fault \
  --input results/17-new-fault --output results/17-new-fault-hardware \
  --warm-resets 0 \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0
```

每份配置需要重新综合/布局布线，最后静态 Fmax 可能变化。实际时钟仍是该份 PLL 目标，不是 Fmax 值。

## 19. campaign.json 是计划，不是已经执行的记录

当前计划包含 54 MHz 不复位一小时、独立十次热复位、27 MHz 不复位十分钟：

```bash
python chapters/17-fpga-stability/campaign.py \
  --serial /dev/serial/by-id/usb-SIPEED_JTAG_Debugger_FactoryAIOT_Pro-if01-port0
```

`campaign.py` 读取每个 case 的 input、seconds、warm_resets，依次调用 `run.py`；结果放在输出目录的场景子目录，顶层 summary 汇总它们。输入 `.fs` 必须事先构建，它不会自动根据 case 名称修改时钟。

当前实际执行时长见下一节，不是 campaign 里的一小时。`17-acceptance` 也不是宣告这整份计划已经运行。

## 20. 本轮实际验收与固定输入

依据 [本轮报告](../../results/17-acceptance/REPORT.md)，2026-10-12 已完成：

| 场景 | 窗口/复位 | RAM 轮数下界 | IRQ 下界 | 回显 | RAM 完成读 / 写下界 |
| --- | --- | ---: | ---: | ---: | ---: |
| 54 MHz 连续 | 600.04 秒，无复位 | 388200 | 599956 | 1165 | 143384 / 1006736447 |
| 54 MHz 热复位 | 60.01 秒，10 次 | 38500 | 59444 | 117 | 19880 / 99849476 |
| 27 MHz 连续 | 120.02 秒，无复位 | 39500 | 119954 | 238 | 16952 / 103441466 |

所有场景未报告错误，结束时无未匹配回显。54 MHz `17-counted` 当前布局的 CPU Fmax 估计约 131.48 MHz；早期 `17` 的估计约 126.34 MHz，属于不同电路/布局结果。

冻结记录保存 RTL/初值哈希、配置与 bitstream 身份，便于从结果找到输入。它不会因为后续重建而自动认证新版本；改动后需要重跑并建立新验收记录。

## 21. 实物环境与其他进阶实验到哪里了？

温度和电压没有自动测量。`--ambient-c`、`--supply-v`、`--measurement-note`、`--board-id` 只是人工记录字段。USB 输入、电源轨、环境温度、芯片表面温度是不同测点；记录一个单点不等于覆盖整个范围。

物理冷启动需要实际断电再上电。当前配置在 FPGA SRAM 中，断电后丢失；应分别记录板卡上电、重新识别/配置和 SoC 启动。软件复位不是这个实验，下载一次 `.fs` 也不是断电证据。小时级、物理冷启动、温压范围目前均未新增通过结论。

17A/17B 已有真实 SMP RTL 的独立仿真，但不继承本章单核的板上结果。17C 参考 Linux-on-LiteX-VexRiscv，尝试中遇到依赖版本/时钟域名称和原生目标固定工具链的问题；记录在 `results/17c-linux/REPORT.md`。带 MMU 的核心、DDR 初始化/训练、设备树、内核、根文件系统仍需独立验证，当前没有 Linux 启动结论。

## 22. 想追查问题，从哪个文件开始？

| 现象 | 先读哪个文件，再追哪里 |
| --- | --- |
| 链接失败/空间不够 | `firmware/link.log` → linker.ld / program.map / 数组与栈预算 |
| 电路生成失败 | elaborate.log / generate.log → Python 外设/CSR/平台定义 |
| 综合失败 | synthesis/synthesis.log → 实际 HDL 清单、原语、Memory 推断 |
| 时序/打包失败 | build/nextpnr.log / pack.log → 目标时钟、资源、器件配置 |
| 识别/下载失败 | detect.log / load.log → USB 附加、器件身份、bitstream 哈希 |
| 没有 BOOT | uart.log → 串口/时钟/复位/ROM/启动路径 |
| BOOT 后没有 PASS | 固件 FAIL/主机 error → RAM、Timer、命令接收或死循环 |
| 只有 RESET 没有 BOOT | 软件请求、CRG rst 连接及 PLL 是否仍供时钟 |
| 一直读同一字符 | UART RX FIFO 消费方式、pending 清除 |
| 读写数量看起来奇怪 | 采样位置、缓存、阶段、十六进制与回绕规则 |

通用的 Builder、固件、仿真与 FPGA 文件说明另见 [文件生成逻辑](../../docs/generated-files/README.md)。本章的关键阅读顺序是：**构建身份 → 地址/软件布局 → 实际串口 → 主机检查规则 → 汇总结论**。
