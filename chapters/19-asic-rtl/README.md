# 19：把FPGA上的SoC改成可用标准单元实现的小核心

前面板上的rPLL、块RAM是FPGA厂商已经造好的资源。换成ASIC后，RTL里不能继续要求制造厂给我们一块Gowin BRAM。本章先选一条能实际运行的路线：**外部时钟、单核VexRiscv minimal、常量逻辑ROM、小容量触发器RAM**。

这是ASIC核心适配实验。封装、供电、ESD、完整pad ring和制造方接收规则仍未冻结，因此结果不称为“可流片的完整芯片”。

## 先看清楚：本章做出的是什么？

```text
外部clk ────────────→ 同一sys时钟域，没有PLL
外部reset_n → 两级复位释放同步器
                       │
                       ▼
                 VexRiscv minimal
                 RV32I，无I/D缓存
                  │iBus     │dBus
                  └───┬─────┘
                  LiteX交叉互连
        ┌──────────┬─────────┬───────────┬──────────────┐
        ▼          ▼         ▼           ▼              ▼
      ROM        SRAM     main RAM    寄存器端点       空CSR窗口
      4KiB       256B       2KiB       GPIO/UART/Timer
   固定逻辑    触发器      触发器       IRQ回到CPU
```

UART这里只有发送器，GPIO只有输入/输出，Timer是一发定时器；这些是本章本地的小外设，不冒充LiteX完整UART/Timer驱动。外设的软件接口是显式Wishbone寄存器，不是前面生成csr.h的那套CSR接口。这次选择用短而可读的RTL，把存储、复位和握手适配的实验范围控制住；完整产品外设接口仍需按规格回归。

### 为什么CPU改成minimal？

当前CPU包中，lite实际上仍带2KiB指令缓存和标签数组。第一次生成的存储清单直接显示了InstructionCache里的banks_0和ways_0_tags。换成minimal后，清单只剩CPU寄存器堆、ROM、SRAM和main RAM。不能从变体名字猜缓存配置。

minimal是RV32I，所以固件的`-march`也改为rv32i。本章不执行乘除指令，不能继续沿用18章候选规格里的RV32IM承诺。本章是一份新的小核心配置，尚未冻结为整芯片产品规格。

## 运行方式

```sh
# 生成RTL，列出所有Memory，映射为通用门/触发器，运行两级功能回归
python chapters/19-asic-rtl/run.py

# 再映射到18章已经固定的ICS55 RVT标准单元，并跑工艺模型仿真
python chapters/19-asic-rtl/run.py --map-cells
```

本次工具版本为Yosys 0.60、Verilator 5.034、OSS CAD Suite内Icarus 14；命令和版本输出保留在工具日志中。

需要18章已下载的PDK。优先使用现有OSS CAD Suite的Icarus/vvp：系统旧版Icarus 10.3不支持PDK IO模型里的rtran电阻开关，新版14可以执行PBMUX的输入、输出、高阻态实验。没有新版时会明确编译失败，不将修改后的简化模型当作原PDK模型。

RAM容量可用`--ram-bytes 1024/2048/4096`选择。这是本教学脚本设置的防误用范围，不是工艺限制；为了避免把几十KiB RAM不知不觉变成大量触发器，暂不允许任意加大。ROM4KiB、SRAM256B、GPIO4位和UART分频8是当前配置选择，也不是ASIC规定的固定数字。

`clk_freq=1_000_000`只是LiteX配置中的频率数值。本章独立测试平台每5ns翻转一次clk，实际仿真时钟为100MHz；UART按每位8个时钟检查，不依赖该配置常量。这里没有用100MHz作为芯片时序通过的结论，也没有做本核心的STA频率签核。

实际数值与逐份日志的读法见 [本次结果解读](RESULTS.md)。

## 每个输入文件负责什么？

| 文件 | 工作 | 产生的结果 |
| --- | --- | --- |
| soc.py | 创建CPU、存储、总线和外设实例 | asic_soc.v里的连接 |
| reset_sync.v | 异步置位、两拍释放复位 | CPU和外设使用的sys_rst |
| peripheral.v | GPIO、UART TX、Timer、结果和阶段寄存器 | 挂在Wishbone上的硬件端点 |
| startup.S | 准备SP、复制.data、清.bss；保存中断现场 | 启动和中断机器指令 |
| main.c | 检查初始化、RAM、字节写、GPIO、UART和IRQ | 固件机器指令 |
| linker.ld | 安排ROM、main RAM、栈和边界符号 | ELF地址布局 |
| tb.sv | 给时钟/复位/输入、独立接收UART、检查完成与超时 | 功能回归日志 |
| pad_pilot.sv | 直接实例化真实PDK PBMUX模型 | IO输入0/1、输出0/1/Z检查 |
| run.py | 串起编译、RTL生成、存储清单、综合、仿真和快照 | results/19全部产物 |

详细代码阅读放在 [逐行理解硬件与构建](HARDWARE_AND_BUILD.md) 和 [固件与启动过程](FIRMWARE.md)。

## results/19里的文件如何产生？

```text
startup.S + main.c + linker.ld
       │ GCC
       ├→ firmware/program.elf、program.map
       ├→ objdump → firmware/disassembly.txt
       └→ objcopy → program.bin → 32位小端列表
                                      │
soc.py + 固件字列表 → LiteX Builder ────┘
       ├→ builder/csr.csv、csr.json、software/include/generated/
       └→ builder/gateware/asic_soc.v + *.init
                     │连同CPU、本地外设、复位源码复制
                     ▼
                  rtl/快照
                     │ Yosys proc/opt，保留未映射存储
                     ├→ rtl/elaborated.v → Icarus → simulation.log
                     │
                     ├→ memories.json → memory-inventory.json
                     │
                     │ memory_map + synth，移除上电init属性
                     ├→ generic.json、rtl/generic.v → generic-simulation.log
                     │
                     │ dfflibmap + abc + ICS55 Liberty（--map-cells）
                     └→ mapped.json、rtl/mapped.v → mapped-simulation.log
```

`elaborated.v`将行为过程转换成寄存器和组合连接，尚未将RAM映射成标准单元。这样也避免原始生成RTL的组合寄存器声明初值在事件驱动仿真起点带来的求值问题。它不是工艺门级网表。最终generic/mapped仿真才检查去掉上电寄存器初值后，实际复位和启动代码能否让电路运行。

`memories.json`和generic/mapped.json是较大的工具中间文件；提交保留紧凑清单、脚本、报告和完整RTL/初始化/库模型。`rtl/sources.json`提供文件哈希。原始RTL、elaborated、generic、mapped是不同表示，编译时分别选对应文件，不能把它们一起作为重复顶层编译。

## 存储怎么变成“能造出来的东西”？

默认配置有：

| 存储 | 宽×深 | 本章实现 |
| --- | --- | --- |
| 启动ROM | 32×1024 | 固件初值综合成常量逻辑，未使用区域的未指定值允许被优化 |
| SRAM | 32×64 | 触发器+读多路选择+字节写控制 |
| main RAM | 32×512 | 同上 |
| CPU寄存器堆 | 32×32，双读单写 | 触发器+读多路选择 |

实际总位数会记录在summary.json。清单来自Yosys的存储对象，不是只用顶层容量加总；CPU内部数组同样算入。

清单中的四个写端口来自32位Wishbone的四个字节写使能，地址和时钟共用，不能解读成四个任意并发访问端口。读端口是否带时钟则是当前Yosys中间表示；某些同步读已拆成“数组组合读+输出触发器”，不能只看RD_CLK_ENABLE就声称源RAM是异步读。

ROM的.readmemh文件只是综合输入，制造后不存在一个会自动打开文件的芯片电路。综合后ROM数据成为门连接中的常量。generic.v和mapped.v不再需要这些初始化文件；回归从这两个网表运行同一固件，验证常量确实保留下来。

RAM没有保证的上电值。generic输出前移除寄存器init属性，工艺单元模型也没有靠仿真预填RAM来通过检查；.data复制、.bss清零、栈分配仍由CPU启动代码完成。

这条路线确实可映射到标准单元，但面积并不一定适合产品。不是已经拿到了ICS55 SRAM宏；取得真实宏后，还要验证掩码、延迟、供电、同址读写和测试接口，再替换这份触发器实现。

## 地址和引脚分别是什么？

| CPU字节地址 | 功能 |
| --- | --- |
| 0x00000000～0x00000fff | ROM |
| 0x10000000～0x100000ff | SRAM |
| 0x40000000～0x400007ff | 默认2KiB main RAM |
| 0x80000000～0x8000003f | 本地寄存器窗口 |
| 0xf0000000起 | LiteX保留的CSR窗口；本章没有CSR业务外设 |

顶层clk、reset_n、gpio_in/out、uart_tx是核心逻辑端口；result[31:0]和stage[7:0]是实验观察口，不是已经分配好的封装引脚。sim_trace由SimPlatform带入，在独立TB中接0，不属于产品接口。

PBMUX实验独立验证了真实IO单元模型，不等于完整SoC已经接好pad ring。供电pad、corner、filler、ESD、输出驱动档位、电压和封装仍需专门确定。

## 如何判断真正跑到了成功位置？

TB不是只看CPU有时钟：它独立从uart_tx接收两个8N1帧，要求是O、K；检查GPIO为9、阶段为6、结果为0x5a。固件还必须通过.data、.bss、32字RAM缓冲区、逐字节写、SRAM首尾地址、栈函数、Timer中断进入和清除。

失败时输出0xe1～0xe8中的错误码，或由TB watchdog结束。summary只有全部要求完成后才写出PASS。若中途失败，不沿用旧summary。

调试中，共享互连+minimal配置出现了完成写未被观察到的问题，本章改为交叉互连后回归通过。交叉互连为各从设备分别仲裁，避免把这个尚未完成根因证明的共享配置当作冻结版；此处不将一次替换配置当作证明LiteX共享互连存在通用缺陷。

## 本章完成和下一章的分界

19验证小核心没有未映射存储或FPGA原语，并能从不同网表表示启动。20再增加重复复位、故障注入、lint、形式安全属性和覆盖率证据。21还需要制造测试与实际综合预算；22以后才有pad ring、布线和物理签核。
