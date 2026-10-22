# 5. LiteX怎样把上游CFU接到真正CPU？

同时打开[soc.py](../soc.py)、[run.py](../run.py)、[litex_builder.py](../litex_builder.py)。所有本章实验Python逻辑都在本章目录；公共tutorial_paths只寻找LiteX源码。

## 5.1 上游文件怎么引进来的？

upstream/manifest.json固定仓库、commit和每个小文件的SHA256。原版CFU和软件头文件直接放在本章，运行时先逐个校验；若有人改了它们却没说明来源，脚本会停止。

fetch_upstream.py的步骤是：读取manifest；若external/CFU-Playground不存在，初始化独立Git目录；添加origin；只fetch指定commit；checkout到该commit；比较上游原件与本章副本的哈希。已有目录版本不符时直接报错，不擅自覆盖用户的其他checkout。

它不递归下载所有子模块、不安装完整TFLM环境、不改系统工具。运行本章不依赖完整checkout，是因为本章所需的原始小文件已随教程保留，而不是只提供一个会消失的外部路径。

## 5.2 最关键的SoCCore参数逐项解释

```python
super().__init__(platform, clk_freq=1_000_000,
    cpu_type="vexriscv", cpu_variant="full+cfu", cpu_reset_address=0,
    cpu_cfu=str(Path(__file__).with_name("upstream")/"cfu_mac.v"),
    integrated_rom_size=4096, integrated_rom_init=rom_words,
    integrated_sram_size=4096, integrated_main_ram_size=16384,
    with_uart=False, with_timer=False, with_ctrl=False,
    ident="CFU tutorial")
```

| 参数 | 含义 |
| --- | --- |
| platform | 定义仿真平台时钟等端口；不是Tang器件的物理管脚表 |
| clk_freq | 本章仿真频率配置；SimConfig也使用1MHz |
| cpu_type | 创建VexRiscv Python包装器 |
| cpu_variant | 选择本地CPU包中VexRiscv_FullCfu.v，它有CFU插件端口 |
| cpu_reset_address | 复位PC为字节地址0，与_start和ROM位置对齐 |
| cpu_cfu | 指定包含module Cfu的源文件；由SoCCore在创建CPU时绑定 |
| integrated_rom_size | 4096字节，不是4096个32位字 |
| integrated_rom_init | 编译后的固件字列表，不是Verilog文件名 |
| integrated_sram_size | 独立4KiB片内SRAM |
| integrated_main_ram_size | 16KiB C数据/栈空间，链接器使用同一容量 |
| with_uart/timer/ctrl | 不加入本章暂不使用的默认组件 |
| ident | 生成系统名称的只读存储；因此结果中还可能有小型mem.init |

这份本地LiteX源码要求：带cfu的CPU变体必须在构造时提供cpu_cfu，否则立即报“CPU CFU variant requires a CFU file/instance”。所以本章没有先构造空CFU CPU、再晚一点加文件。

CPU full+cfu还包含缓存等功能。我们选择它是因为当前CPU包有现成、匹配LiteX接口的RTL，并非神经网络加速器必须使用full配置。若换其他带插件的CPU，必须提供相匹配的生成RTL，不能只改一个字符串就推定支持。

## 5.3 cpu_cfu内部做了哪些硬件连接？

当前LiteX的调用链：

```text
SoCCore(cpu_cfu=文件路径)
  → add_cpu(..., cfu=文件路径)
  → cpu.add_cfu(...)
      ├─ 创建命令/响应Record信号
      ├─ 将CPU插件端口接到这些信号
      ├─ 将Cfu端口接到同一组信号
      └─ platform.add_source把CFU源文件加入工程
```

Record可以理解成一捆带名字的线。它不执行数学计算；计算在原版Cfu模块中发生。

```text
CPU插件输出                          Cfu输入
CfuPlugin_bus_cmd_valid      ───────→ cmd_valid
...function_id             ───────→ cmd_payload_function_id
...inputs_0/1              ───────→ cmd_payload_inputs_0/1

CPU插件输入                          Cfu输出
CfuPlugin_bus_cmd_ready     ←─────── cmd_ready
...rsp_valid               ←─────── rsp_valid
...outputs_0               ←─────── rsp_payload_outputs_0
CPU插件rsp_ready           ───────→ rsp_ready
```

生成的sim.v中可以找到两个实例：VexRiscv和Cfu。它们是并列实例，通过这些线互联；Python中cpu.cfu_bus这种访问写法不意味着CFU一定物理放在CPU实例内部。

## 5.4 命令计数怎样证明用了硬件？

```python
b = self.cpu.cfu_bus
self.sync += If(b.cmd.valid & b.cmd.ready,
    self.commands.eq(self.commands+1))
```

每个命令接受沿计数一次。不能只数cmd_valid为1的周期，因为等待时valid可能连续保持多个周期，同一命令不该重复计数。

响应计数同理看rsp.valid & rsp.ready。本章硬件模式最终观察到619条已接受命令；软件模式0。计数来自实际RTL信号，不是Python根据源码行数猜的。

本章观察计数器为仿真教学增加，不是上游核心原有的业务寄存器；不要求FPGA最后一定保留这些调试电路。

## 5.5 为什么还有Wishbone日志端点？

```python
self.bus.add_slave("trace", self.trace.bus,
    SoCRegion(origin=0x80000000, size=64, cached=False))
```

给固件一个能写报告的地方。写入不同字地址时，Migen生成的Display打印结果；写最后的完成码时Finish结束仿真。地址窗口64字节不是分配64字节RAM。

这里有两条不同路径：

```text
cfu_op0 → CUSTOM0 → CPU插件 → CFU → CPU结果寄存器
TRACE(n)写入 → CPU store → Wishbone → 日志端点 → 仿真终端
```

Display/Finish是仿真观察手段。移到真实FPGA时，需要换成UART、可读寄存器等实际出口，不会在芯片上凭空出现电脑终端。

## 5.6 run.py从哪一步开始真正执行？

1. check_upstream校验源文件哈希。
2. direct_tests编译Icarus独立TB，用Python独立公式生成预期值。
3. build_firmware调用GCC编译startup.S、main.c和software_cfu.c。
4. objcopy导出ROM镜像；objdump导出反汇编；检查CUSTOM0数量。
5. cpu_test调用本地build_and_run，创建SoC与Builder。
6. Builder生成RTL、地址图、头文件及仿真工程。
7. helper编译clocker插件和Verilator CPU模型，再真正运行Vsim。
8. 从实际日志检查13、28、0、随机检查数、命令计数和完成码。
9. 重新编译软件模式，再运行同一配置的SoC。
10. 全部完成后才写summary.json和REPORT.md；失败时不保留旧PASS摘要。

## 5.7 结果目录按生产者看

```text
本章upstream原文件 + tb_mac.sv + Python参考向量
  └→ results/13f/direct/
       ├─ vectors.txt：功能号、两个word、预期结果、响应暂停拍数
       ├─ cfu_cycles.csv：真实握手与结果轨迹
       ├─ mac.log、passthrough.log：独立检查
       ├─ negative/run.log：错误offset被抓到
       └─ 独立实验源码快照：统一放在../rtl/direct/

startup.S + main.c + linker.ld + 原版头文件
  └→ results/13f/firmware/
       ├─ program.elf：链接后的代码、数据和符号
       ├─ program.map：地址由链接器如何分配
       ├─ program.bin/hex：ROM字节/32位字
       └─ disassembly.txt：实际机器指令，包括CUSTOM0

SoCCore + ROM字列表 + Cfu文件
  └→ Builder → results/13f/builder/
       ├─ csr.csv/json：硬件地址和配置
       ├─ software/include/generated/：由该配置导出的头文件
       └─ gateware/sim.v + sim_*.init：顶层与存储初值
             │ Verilator + 本地clocker
             └→ obj_dir/Vsim → run.log

必要RTL和初值另复制 → results/13f/rtl/
  sim.v + VexRiscv_FullCfu.v + cfu_mac.v + 所有.init + sources.json
```

软件模拟模式保存在results/13f-software，固件与运行日志独立，避免覆盖硬件模式。CPU核和CFU连接仍存在，但命令计数0。

rtl/direct中两个CFU都叫Cfu，两个TB都叫tb；按sources.json的实验分组编译，不能用通配符把两个版本同时编进去。

## 5.8 相对路径为什么重要？

生成的sim.v用readmemh("sim_rom.init",...)加载初值。仿真程序启动时的工作目录必须能找到这些文件。本地helper在builder/gateware目录运行Vsim；rtl快照也带齐初值，便于独立复查。

只复制CPU大文件、不复制Cfu或ROM初值，会导致无法链接模块或CPU没有正确固件。本章每次生成sources.json记录实际文件哈希，并检查CPU、Cfu与初始化文件都在快照里。
