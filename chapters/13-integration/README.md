# 第 13 章：把外设接在一起，让整颗 SoC 自检

## 本章结果文件从哪里来？

`run.py` 用配置驱动 `litex_builder.py` 的 `elaborate()`，先生成软件接口，再由 `compile_firmware()` 编译固件并追加本章 ROM 校验信息。`compile_simulator()` 编译宿主仿真器，`run_simulator()` 执行各场景。`manifest.json`、`summary.json`、场景 JSON/日志和 UART 文本由教程脚本记录；Builder 负责电路和原始地址导出。

完整的文件分类、生产者、依赖关系和阅读顺序，见 [文件生成逻辑说明](../../docs/generated-files/README.md)。它是阅读参考；本章运行不依赖其他章节的 Python 文件。

## 本章目标

一颗单核 VexRiscv `standard` 从 ROM 启动，用同一份 C 固件检查 ROM、RAM、GPIO、UART、Timer/IRQ、SPI、I²C，再让中断与串口、存储器和协议访问一起运行。每项结果都经 **LiteX UART 的 TX 引脚**发送，Python 从独立串口采样器的日志重建文本。

这次新增的是整机配置、统一地址/IRQ 分配和跨模块验证。固件判定、端点完成码、引脚协议观察三份证据要一致。仿真使用片上 ROM/SRAM/main RAM；外部 SDRAM、Flash、SD 卡和以太网是后续按资源接入的选项。

## 输入与运行

需要第 00 章列出的 LiteX、Migen、VexRiscv `standard` 数据包、Verilator、支持 C++20 的编译器、RISC-V GCC/objcopy/objdump，以及 `libjson-c-dev`。本章所有逻辑和模型都在当前目录；唯一共用的 `tutorial_paths.py` 负责定位 LiteX。独立复制本章时，脚本也可从已安装的 LiteX 导入。

从仓库根目录执行：

```sh
python chapters/13-integration/run.py
```

默认构建一个仿真器，用同一 ELF/ROM 执行 8 个场景。只运行正常场景：

```sh
python chapters/13-integration/run.py --case normal
```

改变参数并写到另一结果目录：

```sh
python chapters/13-integration/run.py --gpio-width 7 --rom-size 0x2000 \
    --main-ram-size 0x8000 --output results/13-parameters
```

`--seed 13 --seed 97` 指定 UART 复位种子；重复同一参数与种子可复现时机。种子决定起始位之后的延迟，窗口由当前每位时钟数计算。默认时机不是协议规定的常量。

## 概念速查

| 名词 | 本章怎样理解 | 实际位置 |
| --- | --- | --- |
| 整机自检 | 一个程序通过真实访问逐项检查系统 | `main.c` 的 `main()` |
| CSR bank | CPU 通过桥访问的一组控制/状态寄存器 | GPIO、UART、Timer、SPI/I²C |
| IRQ 路由 | 将外设事件送到 CPU 的某一中断输入 | Timer 事件 → 本章分配的 slot 0 |
| 并发 | CPU 执行主程序时，UART 和 Timer 独立推进；IRQ 可打断主程序 | `stress()` 和 `isr()` |
| 现场 | 中断返回后程序继续所需的寄存器和栈状态 | `startup.S` 的 `trap_entry` |
| 配置标签 | 固件和硬件共同持有的配置摘要的一部分 | ROM trailer 和完成端点读值 |
| 完成端点 | 仿真中报告阶段、记录 ISR、终止测试的 Wishbone 从设备 | `CompletionSlave` |
| 仿真控制器 | 注入一次复位、选择故障、限制运行周期 | `sim_control.v`；不属于待流片功能 |

## 谁与谁连接？

```text
VexRiscv standard
  iBus ─┐
        ├─ Arbiter / RoundRobin ── 共享 Wishbone ── Decoder
  dBus ─┘                                            │
                  ┌──────────────────────────────────┤
                  │                                  ├─ ROM：程序、初值、校验尾部
                  │                                  ├─ SRAM：全容量模式与窄写测试
                  │                                  ├─ main RAM：.data/.bss、栈
                  │                                  └─ completion：延迟 ACK、报告结果
             Wishbone2CSR
                  │
             CSR interconnect / CSRBankArray
                  ├─ GPIO 输入：同步后读回仿真输入
                  ├─ GPIO 输出：驱动并观察输出信号
                  ├─ UART：TX ──> 独立采样器 ──> Python 重建文本
                  │        └──> RX：引脚回环，再由固件比较每个字节
                  ├─ Timer：倒计数 ──> event pending ──> CPU IRQ
                  ├─ SPI 引脚 CSR ──> SPI 从设备模型
                  ├─ I²C 引脚 CSR ──> 开漏 SDA 解析与从设备模型
                  └─ identifier_mem：系统名称

sim_control：观察 TX、未完成的总线访问和 IRQ
       └─ test_reset ──> CRG ──> sys 复位
CRG：为系统提供时钟与复位
```

一笔 GPIO 写入走 dBus → 仲裁 → 译码 → Wishbone2CSR → 输出 bank → 输出信号。Timer 的 IRQ 用另一条线通知 CPU；进入 ISR 后，CPU 才经总线读 pending、清事件。`bus`、`csr`、`irq` 管理这些配置与连接，实际事务由生成的仲裁、译码、桥和事件电路处理。

`soc.py` 使用原生 `SoCCore`、`SoCRegion`、`wishbone.Interface` 和 `add_uart`。GPIO 和 Timer 是带显式 CSR 名称的本章适配实现，沿用 LiteX 对应核心的结构；SPI/I²C 是教程的位操作接口与设备模型。串口采样、完成端点和复位控制都是仿真设施，后续 ASIC 顶层需要替换或移除这些设施。

## 数字怎样来的？

[`config.py`](config.py) 是本章参数的统一来源，生成 C 宏、链接脚本、ROM 元信息和结果清单。下表都是**当前配置**，修改后要重新构建。

| 参数 | 默认选值 | 选值理由与改变后的影响 |
| --- | --- | --- |
| `sys_clk_hz` / `baud` | 1 MHz / 100 kbaud | 当前 10 个时钟一位，方便观察；采样器要求整数比且至少 8 个时钟一位 |
| `gpio_width` | 4 位 | 小规模演示；支持 1–32 位，掩码、输入模式与 CSR 位宽随之生成 |
| `rom_size` | 16 KiB | 容纳固件、填充区和校验尾部；链接器另留出尾部空间 |
| `sram_size` / `main_ram_size` | 4 KiB / 16 KiB | SRAM 做模式测试，main RAM 放运行段和栈；容量要求符合本例的区域对齐 |
| `stack_size` / `stack_guard` | 2048 / 16 字节 | 栈预算防止与 `.bss` 重叠；顶部 guard 留给物理末字测试 |
| `uart_fifo_depth` | 4 项 | 本固件逐字节回环，避免报告文本淹没 RX FIFO |
| `response_wait` | 8 个倒计数时钟 | 完成端点先捕获请求再等待，ACK 还有捕获/响应拍；总延迟并非简单等于 8 |
| `timer_period` | 8000 个装载计数 | 给 ISR 足够时间，压力阶段重复触发；按当前实现，周期包含计数到 0 后的重装拍 |
| `stress_bytes` / `minimum_irqs` | 128 字节 / 3 次 | 自定义压力规模；修改后串口预期与协议事务数量一起变化 |
| `poll_limit` / `max_cycles` | 20000 次轮询 / 2000000 系统周期 | 固件等待上限与硬件 watchdog 分别防止无限等待，二者单位不同 |
| SPI command / reply | `0x9f` / `0xa5` | 本模型约定，可在 Config 中改变；不是所有 SPI 设备的共同协议 |
| `i2c_address` | 7 位 `0x42` | 模型与固件一起生成地址；传输字节为地址左移 1 位再加读写位 |

32 位 Wishbone、4 个字节通道和 `-march=rv32im -mabi=ilp32` 来自本章选定 CPU/总线。端点末字地址为 `completion_base + completion_size - sizeof(uint32_t)`；字地址再除以当前一个字的 4 字节。UART 8N1、SPI mode 0/MSB-first 和 I²C 两个寄存器是本例实现的协议范围。ROM 的四字尾部、magic `0x13c0ffee`、成功码 `0x5a`、阶乘输入 6 和 scratch 的 64 个字是本章选定的文件格式与测试激励；改动时需同步修改生成与检查两端。

选定的字节地址图如下；运行器与 Builder 的实际结果逐项比较：

| 区域 | 起点 | 默认大小 |
| --- | --- | --- |
| ROM | `0x00000000` | `rom_size`，当前 16 KiB |
| SRAM | `0x10000000` | `sram_size`，当前 4 KiB |
| main RAM | `0x40000000` | `main_ram_size`，当前 16 KiB |
| completion | `0x80000000` | `completion_size`，当前 4 KiB |
| CSR | `0xf0000000` | 当前 SoCCore 的 64 KiB 窗口 |

`TutorialSoC.csr_map` 显式选择 GPIO input/output、UART、Timer、SPI、I²C、identifier 的页号 0–6。当前 CSR 页跨度为 `0x800` 字节，它来自当前 SoCCore 的 `csr_paging` 默认配置，所以 Timer 基址是 `0xf0001800`。修改页号或页跨度时，也要更新地址验收合同。IRQ 同样是分配结果：Timer slot 0、UART slot 1；固件从生成头文件读取 `TIMER0_INTERRUPT`，UART 的事件使能保持关闭，收发采用轮询。

## 一条命令怎样变成完整仿真？

```text
Config 校验参数
    ↓
第一次 elaborate：定地址与 IRQ，生成 csr.h / soc.h
    ↓
Config 生成 test_config.h / linker.ld
    ↓
GCC 编译 startup.S + main.c → ELF/map → 二进制
    ↓
完整 ROM：程序与 .data 初值 + 填充 + 四个校验字
    ↓
第二次 elaborate：将 ROM 内容放进同一配置，Builder 生成 RTL
    ↓
复制全部 HDL/初始化文件 → results/13/rtl/
    ↓
Verilator 编译一次 → 同一仿真器执行正常/故障/复位场景
    ↓
Python 核对串口、端点、IRQ 与协议日志，汇总 summary.json
```

`elaborate`、`compile_firmware`、`compile_simulator`、`run_simulator` 都是**本章辅助函数**。LiteX `Builder` 负责导出硬件工程与软件接口；教程函数继续调用交叉编译器、make/Verilator、运行进程和检查器。第一遍构造使用一条占位跳转，仅生成头文件，不运行 CPU；第二遍才装入真正固件。

ROM 最后四个 32 位字保存 magic、配置 tag、32 位加法校验和、校验范围字数。固件从 ROM 逐字读取并累加，比较尾部记录，同时读完成端点的硬件配置 tag。配置 tag 是 SHA-256 的前 32 位；完整配置、源码、RTL 和二进制 SHA-256 保存在 manifest。加法校验用于发现本实验的镜像损坏，完整 SHA-256 用于追溯构建版本。

ROM 位于物理地址 0。编译命令中的 `-fno-delete-null-pointer-checks` 让这个裸机实验可以明确读取零地址，避免编译器按常规 C 空指针假设优化访问。`.data` 的 ROM 初值仍由启动代码搬到 main RAM，`.bss` 清零，SP 设为链接器生成的 `__stack_top`。

## 八项自检实际检查什么？

| 编号 | 检查 | 除了固件 PASS，还核对什么？ |
| --- | --- | --- |
| 01 ROM | 完整 payload 校验和、尾部格式和配置标签 | 损坏填充字后必须失败，记录实际加载镜像哈希 |
| 02 RAM | `.data/.bss`、SRAM 全容量模式、字节/半字写、两块 RAM 首末字、递归阶乘 | `MEMORY_BOUNDARY` 证明首末地址确实到达存储器总线；查看函数反汇编 |
| 03 GPIO | 输出寄存器读回与同步输入值 | 实际 `GPIO_OUTPUT` 变化；错误地址场景没有完成该阶段 |
| 04 UART | 报告文本逐字节引脚回环 | 独立采样器重建完整文本；每个发送字节由固件从 RX 比较 |
| 05 Timer | 一次性中断、ISR 清事件、返回后计数保持 | IRQ 上升/下降与一次 `TIMER_ISR count=1` |
| 06 SPI | 片选无效时忽略请求；选中时收发约定字节 | 从设备记录 command 和 16 个采样位 |
| 07 I²C | 不存在的地址 NACK、两寄存器写读、重复 START | 设备日志独立记录 ACK、读写与读末尾 master NACK |
| 08 并发 | 长字符串、周期 IRQ、GPIO 翻转、重复 SPI/I²C、scratch、递归与栈边界 | ISR 位于压力区间，计数连续；计算结果和栈 canary 完整 |

main RAM 的物理末字用于边界检查，因此链接器把 SP 放在 RAM 末端下方的 guard 边界。这样测试不会覆盖当前 main 的返回地址。`trap_entry` 在当前栈上预留 64 字节，保存 RV32 的 16 个调用者保存寄存器，调用 C ISR，恢复后用 `mret` 返回；`mepc` 保存被中断程序的恢复位置，普通函数调用仍使用 RA。启动代码的 `mie=0x880` 选择架构中的 machine external/timer 两个中断类别；本章 Timer 走 externalInterruptArray，单独的 CPU timerInterrupt 接口保持低电平。`mstatus.MIE` 的位 3 和 VexRiscv 源 mask CSR `0xbc0` 分别控制全局使能与这颗核的源选择。64 字节来自当前保存清单，不代表所有中断入口都采用同样大小。

并发有两层：UART/Timer 的状态机与 CPU 独立推进；ISR 随时打断主程序的寄存器操作和等待循环。主程序同时访问多个外设时，iBus/dBus 仍经过仲裁。SPI/I²C 的位操作可能被 ISR 拉长，本模型没有增加固定速率或 clock stretching 的完整验证；后续真实器件要按器件时序重新约束。

正常串口输出的关键部分：

```text
13 BOOT
13-01 ROM PASS
13-02 RAM PASS
13-03 GPIO PASS
UART: integrated loopback
13-04 UART PASS
13-05 TIMER PASS
13-06 SPI PASS
13-07 I2C PASS
STRESS:ABCDEFGHIJKLMNOPQRSTUVWXYZ...（文件中保存全部配置长度）
13-08 CONCURRENT PASS
13 ALL PASS
```

## 故障怎样被捕获？

### 错误 CSR 地址：总线完成了，设备没有按预期改变

`+fault=1` 让固件把 GPIO 输出值写到输入 bank 的只读地址。Wishbone/CSR 桥可以完成这笔事务；输出寄存器保持原值。固件随后读正确的输出寄存器，发现与配置模式不同，发送 `13 FAIL E3`，再写失败码。

```text
SELFTEST_STAGE id=2       RAM 已通过
...                      CPU 写错地址，随后检查输出读值
UART_TX_BYTE ...          重建为 13 FAIL E3
SOC_FAIL data=0x000000e3
```

这里捕获的是设备状态不符。正常 ACK 只能说明访问结束，不能替固件证明地址和含义正确。

### 错误 IRQ 掩码：外设已经请求，CPU 没进入 ISR

`+fault=2` 保持硬件路由不变，让固件错误地使能 `TIMER0_INTERRUPT + 1` 的位。Timer 到零、pending 保持、正确 IRQ 输入拉高，但该输入没有被 CPU 源掩码使能。等待计数的有限循环结束后，固件记录 pending 并报 E5。

```text
IRQ_LINE_ASSERT source=timer0
...                      看不到 TIMER_ISR
IRQ_DIAG pending=1
...                      串口重建为 13 FAIL E5
SOC_FAIL data=0x000000e5
```

检查器同时要求源请求存在、pending 为 1、ISR 缺失与准确失败码。这能定位到中断使能路径。

### 损坏 ROM：CPU 自己发现镜像变化

`corrupt-rom` 场景把完整 ROM 的最后一个 payload 填充字翻转 1 bit，保留执行代码和校验尾部。重新启动同一仿真器时，ROM 从修改后的 `.init` 加载。CPU 累加结果改变，发出 `13 FAIL E1`。运行器在 `finally` 中恢复镜像，每个场景记录实际加载文件哈希。

### 事务中复位：先证明打断了什么，再证明重新启动

默认两颗 UART 种子在起始位后选择延迟，各注入一次复位；另外分别在 `bus_wait=1` 和 `irq=1` 时注入复位。控制器不随 `sys` 复位清零，因此不会不断重复触发。

`reset-bus` 的记录包含：

```text
BUS_WAIT adr=0x20000001 we=0 clocks=          8
RESET_TRIGGER mode=2 seed=13 cycle=...
RESET_ASSERT mode=2 ... bus_wait=1 ...
RESET_RELEASE mode=2 cycle=...
...                      完成新一轮 BOOT 和八项自检
SOC_COMPLETE data=0x0000005a
```

地址 `0x20000001` 是当前 32 位接口的**字地址**，对应字节地址 `0x80000004`，即读取场景控制值。本次复位时端点仍等待，尚未 ACK。检查器只用 `RESET_RELEASE` 之后的新 BOOT、阶段结果与协议事件判定恢复，旧阶段的 PASS 无法凑出新一次成功。IRQ 场景在前一轮已填充 scratch 后复位，main RAM 保留原内容；重启后的 RAM 检查再次要求 scratch 为零，因此这次恢复也会检查启动代码是否重新清 `.bss`。

## Python 怎样追到实际 RTL？

在 `soc.py` 中，下面两段分别定义信号和分配目标区域：

```python
self.bus = bus = wishbone.Interface(
    data_width=32, address_width=32, addressing="word")
self.bus.add_slave(name="completion", slave=self.completion.bus,
    region=SoCRegion(origin=cfg.completion_base,
                     size=cfg.completion_size, mode="rw", cached=False))
```

第一段位于 `CompletionSlave`，`self.bus` 是端点接口；第二段位于 `TutorialSoC`，`self.bus` 是 SoC 总线管理器。前者产生 `adr/dat_w/dat_r/cyc/stb/we/sel/ack/err` 等信号，后者让 Decoder 将匹配区域的请求送到该接口。

在 `results/13/rtl/sim.v` 搜索 `builder_socbushandler_decoder`、`completionslave` 和 `roundrobin`，可以找到区域比较、请求门控和 ACK 选择。搜索 `remaining` 及 `BUS_WAIT`，可定位捕获请求、等待和应答的时序逻辑；搜索 `Wishbone2CSR` 所在层级，沿其信号追到 GPIO/UART/Timer bank。生成名字可能带数字后缀，以当前输出为准。

`VexRiscv.v` 是独立 CPU RTL；`sim.v` 实例化它并连接 LiteX 生成的系统。`i2c_device.v`、`sim_control.v` 通过 `platform.add_source` 登记，再通过 `Instance(...)` 接入。运行器枚举实际 HDL source list，连同所有 `.init` 文件一起保存；`sources.json` 给出来源及内容哈希。FST 波形需要编译跟踪支持和运行时 `sim_trace=1` 两部分，本章都明确配置。

## 输出与验收

默认输出放在 `results/13/`：

| 文件 | 用途 |
| --- | --- |
| `config.json` | 本次选定的参数 |
| `firmware/test_config.h`、`linker.ld` | 从配置生成的 C 常量和链接布局 |
| `firmware/program.elf/.bin`、`program.map`、`disassembly.txt` | 固件、段地址、栈边界和机器指令 |
| `firmware/rom_init.hex` | 包含填充与校验尾部的完整 ROM |
| `builder/csr.csv`、`memory_map.csv`、`irq_map.csv` | 实际硬件地址、权限和中断分配 |
| `rtl/`、`rtl/sources.json` | 完整 HDL、初始化文件与来源；可提交到 Git |
| `manifest.json` | 工具/库版本，配置、源码、RTL、地图和固件哈希 |
| `cases/<场景>.log/.uart.txt/.fst/.json` | 原始日志、串口文本、真实波形与场景记录 |
| `summary.json` | 每个已通过场景及其预期失效/复位条件 |

总入口只在全部选定场景通过后打印 `PASS 13-INTEGRATION`。负例的 PASS 表示检查器发现了指定失效，日志中的 CPU 结果仍是 FAIL。正常完成码在端点接受最后写请求时结束仿真，验证范围截至该写入；此前串口和回环已经完成。

排查时先看 `elaborate.log/link.log/compile.log` 区分构建失败，再看场景日志最后一个阶段。ROM 错误检查镜像、tag 和容量；E5 检查 IRQ 线、pending、CPU mask 和 ISR；I²C 错误检查地址/第九位/重复 START。调小超时或改大压力规模后，重新确认固件和 watchdog 的预算，保留原始失败日志。

## 把自检扩展成测试工具

`run.py` 是固定验收集；`campaign.py` 是本章自己写的压力回归工具。它复用 LiteX 生成的 SoC 和 Verilator 仿真器，一次编译后运行多组场景。LiteX 提供 RTL 生成和 `coverage=True` 编译选项；场景选择、结果核对、覆盖清单与失败重跑由我们实现。

```text
测试种子 + 运行预算
         |
         v
查看未命中的功能点 --> 选择下一场景 --> 保存完整场景参数
         ^                                  |
         |                                  v
   更新覆盖清单 <--- 独立核对日志 <--- CPU 执行随机工作负载
                         |                  |
                         |            UART / SPI / I2C / SRAM
                         |                  |
                         +--------- 真实引脚和总线监视器
                         |
                   失败记录 + 重跑入口
```

工具里的几个函数对应这条流程：

| 函数 | 工作 | 是否改变 RTL |
| --- | --- | --- |
| `plan_case()` | 根据未覆盖项和种子选择场景，保存 plusargs | 不改变；选择运行输入 |
| `execute()` | 启动仿真器，核对结果、实际时钟数与覆盖文件 | CPU 和外设执行真实 RTL |
| `observe()` | 从已经通过核对的总线/引脚日志提取功能覆盖点 | 被动观察 |
| `memory_scoreboard()` | 按字节使能更新参考内存，比较实际读回 | 被动参考模型 |
| `code_coverage()` | 合并 Verilator 计数，生成 LCOV 和源码标注 | 插桩在编译时开启，运行后汇总 |

### 随机化了什么？

固件使用 xorshift32 生成可复现的操作序列。每轮发送一个随机可打印 UART 字符，并选择 GPIO 写读、SPI 命令、I²C 寄存器写读、SRAM 随机地址写读之一。SRAM 操作先写完整字，再随机选择一个字节通道覆盖，最后读回；后台 Timer 周期中断，主程序仍检查 scratch、递归计算和栈底 canary。

Python 独立生成同一序列，检查实际执行的操作和串口字符，不接受只打印一个“随机测试 PASS”。SPI 帧数量、I²C 写读数量必须与操作序列一致。SRAM 监视器记录真实地址、`sel`、写数据和读数据：Python 检查随机写入的地址和字节通道，再维护参考内存核对总线读回。CPU 的缓存可能让一次软件读命中缓存，另一次读触发整条 cache line 填充，所以不能假定“一次 C 读必然对应一次总线读”；软件读值和实际总线读值分别检查。

每个场景还随机选择 Timer 周期、完成端点的 Wishbone 应答等待拍数、复位脉宽、复位次数和触发阶段。复位可以打断 UART 起始位后的不同位置、尚未应答的总线请求、已经拉高的 IRQ；也可以在并发压力阶段重复复位。复位后必须重新启动并完成全部自检。

运行参数通过仿真端点读回，启动代码与 ROM 镜像不需要为每个种子重新编译。端点的偏移 `+16/+20/+24` 分别读随机种子、压力轮数、Timer 周期；`+32` 写本轮操作证据。它们是本章选定的测试接口，不是 LiteX 自带的标准寄存器。

### 如何 capture 到错误？

| 检查层 | 观察什么 | 怎样判失败 |
| --- | --- | --- |
| 固件 | 外设读值、RAM、scratch、栈、ISR | 写具体错误码，不得同时写成功码 |
| 被动总线监视器 | 完成端点与 SRAM 的实际 Wishbone 信号 | 等待时地址/写数据/字节使能改变、无请求 ACK、ACK 与 ERR 同时有效，立即终止 |
| Python 参考模型 | 随机操作、UART 解码、协议帧、SRAM 数据 | 序列、次数、地址、字节掩码或读回数据不同，报告具体场景 |
| 复位检查 | `RESET_ASSERT` 当拍的阶段、`bus_wait`、IRQ | 没打断目标状态，或最后一次复位后没有完整启动，判失败 |
| 运行预算 | 实际时钟数、仿真 watchdog、墙钟超时 | 超时不能作为通过；未达到累计运行量则回归未完成 |

检查器本身也有反例测试：故意篡改读回数据，必须被 SRAM 参考模型抓到；在没有已知写入的情况下读一个地址，不能凭空算作数据检查已覆盖。

### 两种覆盖率分别回答什么？

**功能覆盖**目前定义 44 个点：正常启动、三种故障、长程工作负载、不同复位位置和重复复位、不同等待长度、并发 ISR、I²C NACK、内存边界与参考模型、4 类随机操作、16 种相邻操作组合、4 个字节通道。每个命中点记录场景名，能回到日志核对。

工具优先选择尚未覆盖的故障或复位场景，再在合法范围内随机参数。达到最少场景数、覆盖清单全部命中、实际累计时钟数达到目标后，才报告 PASS；达到 `--max-cases` 仍有缺口则报告 INCOMPLETE，退出码为 2。这是按照功能覆盖缺口选择场景，尚未实现依据 CPU 内部未覆盖 RTL 分支自动求解输入。

**RTL 代码覆盖**由 Verilator 插桩得到，汇总每个文件的分支/行、信号翻转等实际计数，并生成带未命中位置的源码。44/44 功能覆盖不等于 RTL 100% 覆盖。复位、初始化产生的 RTL 计数也保留在原始数据中；报告不会把它们说成全部来自随机压力阶段。覆盖类型随本机 Verilator 版本确定，工具记录版本。详见 [Verilator 覆盖率说明](https://verilator.org/guide/latest/simulating.html#coverage-analysis)。

### 怎样运行和加大规模？

在教程根目录运行：

```bash
python chapters/13-integration/campaign.py
```

默认至少运行 16 个场景，最多 32 个；普通场景随机执行 256–512 轮，长程场景执行 4096 轮；要求累计实际运行至少 2,000,000 个系统时钟。**这些都是本工具的可调默认值，不是“充分验证”的固定标准。** 每轮均含 UART 和一种随机操作；操作数量随种子变化。单场景 watchdog 默认 100,000,000 个时钟，墙钟超时 600 秒；watchdog 上限与实际运行量分别报告。

更大的回归，例如：

```bash
python chapters/13-integration/campaign.py \
  --seed 20261007 --cases 64 --max-cases 96 \
  --iterations 1024 --long-iterations 16384 \
  --min-cycles 20000000 --timeout 1200 \
  --output results/13-nightly
```

改变硬件参数要重新构建，可指定 `--gpio-width`、`--uart-fifo-depth`、`--rom-size`、`--sram-size`、`--main-ram-size`、`--stack-size`、`--sys-clk-hz` 和 `--baud`。运行时改变等待与 Timer 周期不需重新构建。时钟与波特率仍须满足本章串口监视器的整数分频约束。新回归使用新的输出目录，保留旧证据。

### 失败怎样重跑？

每个场景在执行前写入 `cases/case-NNNN.plan.json`，包括种子和全部运行参数。失败时写 `failure.json`，其中有具体异常和重跑命令。原构建和源文件没有变化时，可直接重用仿真器：

```bash
python chapters/13-integration/campaign.py \
  --output results/13-campaign --reuse-build \
  --replay results/13-campaign/cases/case-0003.plan.json
```

重跑结果另存为带时间戳的文件，原失败日志保留。源文件、硬件参数或仿真器哈希变化时拒绝重用。需要波形时，在新目录重新构建同一场景：

```bash
python chapters/13-integration/campaign.py --trace \
  --output results/13-replay-wave \
  --replay results/13-campaign/cases/case-0003.plan.json
```

若原场景改变了硬件参数或 watchdog，重跑也要传入相同参数。默认压力回归不保存每轮 FST；`--trace` 会开启全程波形，长程运行的磁盘占用明显增加。

主要输出在 `results/13-campaign/`：

- `campaign-summary.json` / `REPORT.md`：场景结果、实际时钟数、功能覆盖缺口和 RTL 覆盖。
- `cases/*.plan.json` / `*.log` / `*.uart.txt` / `*.cov`：可重跑的场景与原始证据。
- `coverage/merged.dat` / `merged.info` / `annotated/`：合并的 Verilator 覆盖计数、LCOV 和源码标注。
- `campaign-build.json`：源文件、固件、仿真器哈希和工具版本；`rtl/` 保存完整 HDL 与初始化镜像。小体积的汇总报告与完整 RTL 纳入版本管理，原始覆盖数据、日志与波形留在本地。

### 现在的测试范围

当前随机回归覆盖单核片上 ROM/RAM、GPIO、UART 回环、Timer IRQ、SPI 与 I²C，以及仿真端点的等待与复位恢复。UART 每发一字节就等待读回，FIFO 满/溢出尚未构造成覆盖点；SPI/I²C 的数据内容仍采用已知寄存器模式，时钟拉伸、仲裁、总线卡死恢复没有接入。外部 SDRAM/Flash、DMA、多主设备、多核也不在这套场景里。扩展时先增加响应模型、可观察事件与参考检查，再加入覆盖清单。

## 本机验证记录

2026-10-07，当前代码完成了以下实际验证：

| 检查 | 实际结果 |
| --- | --- |
| 固定验收集 | 默认配置 8 个正常、故障与复位场景全部通过 |
| 硬件参数变化 | 7 位 GPIO、8 KiB ROM、32 KiB main RAM 的正常场景通过 |
| 默认压力回归 | 种子 1301，16 个场景，实际运行 10,108,365 个时钟，44/44 功能点命中 |
| RTL 覆盖 | CPU 分支 894/1008，88.69%；SoC 顶层分支 228/250，91.20%；具体缺口见源码标注 |
| 重用仿真器重跑 | 同一场景仍运行 479,781 个时钟并通过，原场景文件保留 |
| 本章独立复制与波形重跑 | 临时目录没有其他章节和共享路径文件，仅指定 LiteX 路径；三次复位场景通过，实际 712,680 个时钟 |
| 检查器反例 | 篡改 SRAM 读回值被抓到；未知地址读值不能算已检查；PRNG 独立向量核对通过 |
| 工具异常路径 | 非法控制参数触发真实仿真错误，日志、场景参数和重跑命令被保存 |
| 覆盖/预算不足 | 只运行一个场景，实际 43,417 个时钟、1/44 功能点；工具返回 INCOMPLETE 和退出码 2 |

完整压力汇总在 `results/13-campaign/REPORT.md`，基础验收和参数实验在 `results/13/` 与 `results/13-parameters/`。独立目录的波形重跑放在 `results/13-replay-wave/`；这次 FST 约 1.1 GiB，大小取决于场景、运行量和信号活动，不是固定需求。

默认正常验收场景本次观察到 6 次连续 ISR。验收依据是一次性中断一次，以及压力阶段至少 `minimum_irqs` 次，并检查 ISR 确实位于压力区间；6 是此次观测值。上述千万时钟规模是本次执行证据，更大的长期回归仍需按目标预算实际运行。

## 本章速记

- 地址、IRQ 和位宽是当前配置；生成头文件、固件和检查器必须使用同一配置。
- ACK 结束总线访问，设备功能是否正确还需要读值或引脚证据。
- 外设发出 IRQ 后，源使能、CPU 掩码、全局中断使能和入口代码共同决定 ISR 是否运行。
- 整机压力测试检查模块重叠运行时的状态与现场；结果通过日志、串口和波形交叉核对。
- FPGA/ASIC 迁移继续沿用这份软件自检，同时落实真实 IO、存储、时钟与制造测试入口。

## 进入下一章

保留本次配置、固件、完整 RTL 和通过记录，作为 FPGA 与 ASIC 的功能基线。13A 将增加独立的 JTAG/TAP 实验；其测试入口与本章固件自检的访问范围需要分别解释。

若要观察同一整机在开源与商业仿真器上的编译和运行耗时，参见 [13E 工具对照附录](../13e-tool-comparison/README.md)。
