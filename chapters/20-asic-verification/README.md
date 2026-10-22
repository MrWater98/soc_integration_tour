# 20：怎样证明19章的ASIC核心确实按预期工作？

19章跑通了一条路径：CPU从ROM启动，测试RAM、GPIO、UART和Timer，写成功码。20章继续问：如果复位发生在中间呢？如果RAM不应答呢？如果只看一次PASS，漏掉了多少行为？

本章保留能实际执行的检查，把每个结果与它能证明的范围一起记录。**当前是验证工作包通过，不是生产验证已经冻结。** 专用CDC/RDC、全CPU等价、完整覆盖收敛和布局后多角时序仍未完成。

## 运行与输入

```sh
python chapters/19-asic-rtl/run.py --map-cells
python chapters/20-asic-verification/run.py
```

20章以19章生成的RTL快照为输入，不导入19章的Python逻辑。run.py先把输入复制到`results/20/rtl/`，后面的编译、故障注入、lint和覆盖率均使用这份副本。可以用`--input`指定另一份完整快照，用`--output`隔离结果。

默认重复启动8次，可用`--boots`修改。8是本实验默认计数，不代表已经完成数小时稳定性测试。硬件仍是19章的RV32I、默认2KiB工作RAM、4位GPIO等配置，不能把旧章节RV32IM/大RAM的结论直接搬过来。

## 一、需求先对应到测试

| 需求 | 正常检查 | 边界/中断/故障检查 | 证据 |
| --- | --- | --- | --- |
| CPU从ROM进入C | 冷启动到0x5a | 多次复位后重新执行.data/.bss初始化 | cold.log、repeated-reset.log |
| RAM读写与字节使能 | 32字不同值、四次单字节写 | 读数据强制为零，预期e1；无ACK，预期watchdog | fault-ram-data.log、fault-no-ack.log |
| SRAM地址范围 | 首字、末字分别读写 | 256B容量对应末字0x100000fc | 固件及冷启动日志 |
| GPIO | 输入5，输出9并读回 | 输入错误，预期e5 | fault-gpio.log |
| UART TX | 从引脚独立解出O、K，检查停止位 | 业务阶段复位后重新发送 | 各正常系统日志 |
| Timer IRQ | 进入一次ISR，清源后不重复 | 屏蔽IRQ，系统watchdog发现未完成 | fault-irq-masked.log |
| 复位释放 | 两个上升沿后释放 | 九次异步置位/相位试验 | reset-phase.log |
| 请求完成 | ACK只在cyc&stb时出现 | 去掉ACK请求门控，形式检查必须失败 | formal.log、formal-negative.log |
| 外设写入语义 | 整字写/读回 | 部分写、无效寄存器、随机空闲和复位中断 | stress-*.log |
| 综合保持关键功能 | generic和ICS55 mapped分别启动 | 两次启动、RAM无上电init依赖 | generic-run.log、mapped-run.log |

本表也显示缺项：没有穷举CPU指令和异常，没有完整物理RAM March，没有UART RX，因为当前核心没有实现接收器。不能把未实现功能写成覆盖率0%后仍说它已经验证。

## 二、系统测试平台如何判断结果？

打开[tb.sv](tb.sv)。

```verilog
asic_soc dut(.sim_trace(1'b0), .*);
always #5 clk=~clk;
```

实例化被测核心；仿真追踪输入接0；每5ns翻转时钟，完整周期10ns。这个仿真频率不证明芯片能跑100MHz，STA需要另外做。

```verilog
if($value$plusargs("BOOTS=%d",required_boots)) begin end
```

从运行命令读取`+BOOTS=8`。它只控制测试平台重复多少次启动，不改变芯片RAM大小或固件机器码。

```verilog
if(cycles>100000*required_boots) $fatal(1,"WATCHDOG ...");
```

设置仿真周期上限。超过限制即失败，因此总线永久无应答不会让测试无声挂住。这个上限是教学测试预算，可随固件工作量重新评估。

```verilog
if(cycles>5 && reset_n && (^{uart_tx,gpio_out,result,stage} === 1'bx))
    $fatal(...);
```

对外部可观察信号做四态未知值检查；先跳过复位初期。归约异或遇到X/Z会产生X，用全等比较检测。它没有检查CPU所有内部寄存器；未使用的RAM允许保持未知。

UART接收器等uart_tx下降沿找到起始位，然后等待1.5位时间采第一数据位，每隔一位再采一次。八位后检查停止位为1。它和发送器共享配置的位周期，但不读取发送器内部状态。

结果非零时必须同时满足：结果等于0x5a、GPIO为9、阶段6、已完整解出两个字符。否则即使某条线误变成0x5a，也不能记成功。

### 复位案例究竟注入在什么时候？

`+RESET_STAGE=2`在RAM测试阶段开始时拉低复位，`+RESET_STAGE=5`在Timer配置阶段开始时拉低复位，再重新释放。它们验证**系统阶段中的重新启动**，不是证明每一种总线流水线位置都试过了。

另一个stress_tb专门把复位置于尚未被ACK接受的请求中，检查事务取消和状态恢复。二者覆盖的时点不同。

## 三、故障注入怎样接到实际RTL？

编译系统TB时增加`-DRTL_FAULTS`，才会包含内部force路径。generic/mapped的正常回归不包含这些路径，避免把原RTL层级名错误套在展平网表上。

| +FAULT | 注入位置 | 意图 |
| --- | --- | --- |
| 1 | 顶层实际RAM读数据interface2_dat_r | 把读数据强制为0，破坏.data变量检查 |
| 2 | 主RAM应答interface1_ram_bus_ack | 阻止一次RAM访问完成，验证超时检测 |
| 3 | 外设连到CPU的IRQ信号registers | Timer有pending但CPU收不到请求 |
| 4 | TB给GPIO输入0而不是5 | 验证固件的GPIO输入检查 |

这些名称以本次elaborated.v为准。曾经向一个已被Yosys折叠的别名sram1_memory11注入，实际消费者没有受影响，系统照样PASS；所以改为直接force真正参与读数据选择的interface2_dat_r。**故障脚本必须要求看到指定错误，不能只因为执行过force就算检测成功。**

IRQ屏蔽案例使用系统watchdog作为本次预期检测点。固件本身也有等待上限，但CPU执行该循环的周期数可能超过TB预算，因此这里不能伪称观察到了e6。

## 四、随机压力怎样避免“随机跑一跑就说没事”？

[stress_tb.sv](stress_tb.sv)直接驱动本地peripheral，不包含CPU。默认运行三个固定seed：1、7、19，每个10000次请求。

随机变化的是：

- 五类地址：GPIO输入、GPIO输出、result、stage、未实现地址8。
- 读或写。
- 整字sel=1111或部分写sel=0001。
- 32位写数据。
- 请求之间0～5个空闲时钟。

固定计数每113次请求，在首个接受沿之前插入复位。测试平台维护独立的model_result、model_gpio、model_stage；每拍检查DUT寄存器，读事务还要对比预期读值。

### 一笔事务按什么顺序执行？

```text
设置地址/数据/sel/we
 → 置cyc、stb
 → ACK未出现：保持字段不变，继续打时钟
 → ACK出现：读取并比较返回数据
 → 在接受沿更新独立模型、检查DUT
 → 撤销请求，再进入随机空闲
```

不能在等待期间不停换地址，否则不再是本端点接受的Classic事务。

测试还要求20个功能bin都有命中：`5种地址 × 读写2种 × sel类别2种`。每个seed未命中任意一项都会失败，日志列出每个bin次数。**这20项只覆盖本压力模型选定的寄存器组合**，不是全部UART/Timer状态、所有sel位型或SoC总线流量。

请求数包含被复位中止的请求；例如默认10000次里有89次中断，不能把10000全部称为成功完成事务。summary保留请求数，日志保留reset_aborts。

## 五、形式属性逐句看

[properties.sv](properties.sv)不按C固件走固定路径，而将总线输入声明为任意值：

```verilog
(* anyseq *) reg reset,cyc,stb,we;
```

对有限的12步模型搜索，工具可以选择所有可能的这些输入值，而不是只采样几个随机种子。

```verilog
reg past_valid=0;
if(!past_valid) assume(reset);
```

第一步假定复位有效，让被验证的寄存器有定义状态。这是明确的验证前提，不是工具凭空证明了上电一定复位。

```verilog
assert(!ack || (cyc && stb));
```

如果ACK为1，必须确实有有效请求。它直接防止没有请求时冒出应答。

```verilog
if($past(reset)) assert(result==0);
```

如果上一拍复位有效，那么现在结果寄存器应为0。`$past`表示前一个采样周期，不是当前组合输入。

```verilog
if($past(cyc && stb && ack && we && sel==15 && adr[3:0]==6))
    assert(result==$past(dat_w));
else assert(result==$past(result));
```

上拍完成对结果寄存器的整字写，本拍应出现对应写值；否则保持原值。这同时检查部分写不会误改result。对pending寄存器还检查W1C后IRQ清除。

工具链执行：

```text
read_verilog -formal -sv  读取RTL和假设/断言
prep ... -flatten        展开为一个待证明模块
async2sync               将边沿相关模型转为本检查使用的采样表示
chformal -lower          将当前Yosys的check对象转换成SAT支持的断言对象
sat -seq 12 ...          对12步展开求解；反例或未完成会失败
```

这不是无限时间的归纳证明，也没有证明CPU。另造一个坏版本，将`assign ack = request && response_ready`改成`assign ack = response_ready`，同一套属性必须找出反例。如果正常和坏版本都PASS，检查本身就值得怀疑。

## 六、lint、CDC、RDC分别做到哪一步？

Verilator lint读取原始生成顶层和完整CPU，不只读外设小模块。脚本阻止LATCH、MULTIDRIVEN、UNOPTFLAT；已列出的宽度/CASEINCOMPLETE告警计数写入summary并逐类解释，其他新类别会让脚本失败；不能把`-Wno-fatal`误读为没有告警。

当前单一sys时钟域的边界：

| 来源 | 目标 | 处理 | 当前证据 |
| --- | --- | --- | --- |
| 外部clk | CPU/总线/存储/外设 | 直接同域 | RTL连接、综合单元时钟清单 |
| 外部reset_n | reset_sync | 异步置位，两个触发器释放 | reset_phase九组试验 |
| GPIO输入 | gpio_meta→gpio_sync | 两级同步 | RTL结构、功能仿真；未做模拟亚稳统计 |
| Timer IRQ | CPU外部IRQ | 同一sys域 | 中断进入、清源、次数检查 |
| UART TX | 外部接收器 | 输出串行信号 | 独立引脚解码 |

本地clock_audit.py还会读取通用网表，重新执行Yosys过程展开，逐个核对存储单元的CLK引脚是否接到顶层clk，结果为clock-domain-audit.json。它检查的是实际连接，而不是看到模块都叫sys就猜它们同域；对应中间网表保存在本地clock-structure.json。

没有专用CDC/RDC工具签核，不能根据“只有一个主时钟”就宣布所有复位域、电气恢复时间和同步器放置都通过。多位GPIO也只保证各位同步，不保证跨位一致采样。

## 七、代码覆盖率怎么来的？

coverage.cpp用Verilator模型真正运行同一份ROM固件，不是从源代码数几个if：

```cpp
soc.clk=0; soc.eval();
soc.clk=1; soc.eval();
```

给一次低电平和高电平求值，推进一个时钟。起初保持reset_n=0，随后释放。看到结果后写coverage.dat，要求结果为0x5a。

本地coverage.py用`--coverage-line`只插入行覆盖记录，再用`verilator_coverage --annotate-min 1`输出带标注源码和coverage.info。脚本逐条数LCOV的DA行命中数，summary给出`lines_hit/lines_total`，门槛是至少命中一次。

这里的分母是工具插入行覆盖点对应的源码行，不是源文件总行数，更不是执行过的RISC-V指令种类数。没有插桩的空行、声明不进入分母。不能把`--coverage`混合产生的信号翻转计数也当作“这行代码执行了”：本章因此单独使用line模式，并在coverage-summary.json记录模式。

可单独运行`python chapters/20-asic-verification/coverage.py`重新生成这项记录，不必重做前面的门级回归。

覆盖率来自**一次正常固件运行**。故障与随机外设仿真使用Icarus，未混入这份Verilator覆盖统计；不能拿它的百分比代表所有回归用例的合并覆盖率。未命中的CPU分支可能是未执行指令、异常或错误路径，必须单独分析，不能自动全部豁免。对应的待办和告警说明见[检查缺项与豁免原则](WAIVERS.md)。

## 八、result里的文件关系

```text
19/rtl快照 → 20/rtl副本 → Icarus编译系统TB
                               ├→ 正常/重复复位/阶段复位日志
                               ├→ 故障指定错误日志
                               └→ generic/mapped两次启动日志
peripheral.v + stress_tb.sv → 三个seed压力日志、功能bin计数
reset_sync.v + reset_tb.sv → 复位相位日志
peripheral.v + properties.sv → formal.log + 破坏版formal-negative.log
原始顶层 + 完整CPU → Verilator lint.log
原始顶层 + 完整CPU + coverage.cpp → coverage.py行模式 → coverage.dat → coverage.info/annotated/
全部检查 → summary.json；文件哈希 → rtl/sources.json
```

运行开始先删除旧summary，只有完成全部要求后才生成新summary。日志没有PASS、错误签名不对、形式负例没有失败、覆盖数据为空，都会让脚本停止。

## 本章状态怎么读？

- 正常运行、指定故障、随机外设、有限步属性、复位和网表功能回归：可以根据日志判断PASS。
- 生产验证冻结：OPEN。没有完整顺序等价、专用CDC/RDC、完整指令/异常覆盖、长时间整机压力和物理时序检查。

下一章20A用独立扫描链和小RAM讲制造测试基础；它不替代本章功能验证，也不会自动把本SoC改造成扫描可测设计。

## 课堂回顾

1. 故障注入后程序仍PASS，为什么可能是注入点选错，而不是程序很健壮？
2. 20个随机功能bin的分母从哪里来？哪些行为没有计入？
3. `sat -seq 12`和无限时间证明有什么区别？
4. 为什么去掉ACK请求门控的坏版本也要跑形式检查？
5. 为什么有代码覆盖率报告，仍然不能宣布验证冻结？

## 一个实际踩到的坑：覆盖率程序启动了，却没有运行固件

第一次运行coverage模型时，把工作目录设成`results/20/`，而ROM文件在`results/20/rtl/`。日志出现：

```text
%Warning: asic_soc_rom.init:0: $readmem file not found
```

可执行文件本身可以启动，但没有正确的指令镜像，最终无法得到完成码。修正方式是**在rtl目录启动仿真器**，并把coverage.dat输出路径作为绝对路径传给C++程序。C++中这一行：

```cpp
VerilatedCov::write(argc>1 ? argv[1] : "coverage.dat");
```

表示优先使用命令行给出的输出位置；没有传入才用当前目录。工作目录决定.readmemh相对文件名从哪里查找，输出路径则决定覆盖数据库写到哪里，两者各自明确后才得到真实执行覆盖数据。

## 本次实际结果与覆盖率口径

本次默认回归完成13个系统/故障/随机案例，加上九组复位相位检查、lint、时钟连接审计、正常/破坏版形式检查和单独覆盖运行。全部已实现检查通过；生产冻结仍为OPEN。

| 项目 | 实际结果 |
| --- | --- |
| 默认重复启动 | 8次，最后完成时34697个TB计数周期 |
| 随机外设 | 3个seed，共30000次请求，267次复位取消，29733次完成 |
| 功能bin | 每个seed均20/20 |
| 时钟连接 | 20515个存储单元CLK均接顶层clk；含2个异步复位触发器 |
| lint | 17条宽度扩展、4条截断、1条case不完整，来源逐类说明；无接受的锁存/多驱动/组合环 |
| 形式检查 | 正常版12步通过，ACK坏版本产生反例 |
| 纯行模式LCOV | 1854/2073行至少有一个覆盖点命中，89.44% |
| 更严格的annotation口径 | 1770/2073行的所有关联覆盖点都命中，85.38% |

同一源码行可能关联多个插桩点。当前Verilator的LCOV DA使用该行最大计数，annotation则用最小计数判断是否完整，因此两种结果不同：某个if所在行的一个分支运行过，不代表同一行关联的其他分支也运行过。annotated文件中空格表示全部达标，`~`表示部分命中，`%`表示都未达到门槛。

coverage-summary.json同时记录两种分子/分母。本工具版本的终端百分比有整数舍入，阅读时以计数为准，脚本另计算小数；不能选一个更高的数字就宣称覆盖收敛。
