# 硬件和构建脚本：逐句接到真实RTL

先打开[soc.py](soc.py)。这一章依然由LiteX集成CPU和互连，外设用本地Verilog实例接入。

## 1. SoCCore这一组参数在决定什么？

```python
super().__init__(platform, clk_freq=1_000_000, bus_interconnect="crossbar",
    cpu_type="vexriscv", cpu_variant="minimal", cpu_reset_address=0,
    integrated_rom_size=4096, integrated_rom_init=rom_words,
    integrated_sram_size=256, integrated_main_ram_size=ram_size,
    with_uart=False, with_timer=False, with_ctrl=False, ident="")
```

逐项理解：

| 参数 | 本章选择的含义 | RTL后果 |
| --- | --- | --- |
| platform | 本章定义的逻辑端口集合 | 生成clk/reset_n/GPIO等顶层端口 |
| clk_freq | 写进LiteX配置的频率数值 | 不产生PLL，也不决定TB的时钟周期 |
| bus_interconnect | 选择交叉互连 | 每个从设备有自己的请求选择/仲裁，CPU两路可访问不同目标 |
| cpu_type | 选择Python CPU包装器 | 实例化VexRiscv模块 |
| cpu_variant | 使用包中的minimal预生成RTL | 该版本无缓存，ISA为RV32I |
| cpu_reset_address | CPU复位后从字节地址0取指 | 连接externalResetVector |
| integrated_rom_size | 4096字节启动ROM容量 | 32位×1024字的存储对象 |
| integrated_rom_init | Python整数列表 | 生成ROM.init，再由综合工具读取 |
| integrated_sram_size | 256字节辅助SRAM | 本章测试首字和末字 |
| integrated_main_ram_size | 参数化的工作RAM容量 | 链接脚本使用同一个ram_size |
| with_uart/timer/ctrl | 不加入LiteX默认这三个组件 | 使用本地寄存器端点中的小外设 |
| ident | 空字符串 | 不创建保存系统名称的额外Memory |

这些值是本章实验决策；并不是在ASIC中ROM就必须4KiB或GPIO必须4位。容量是字节，Wishbone adr是字索引，寄存器数据是32位，三个单位不能混用。

## 2. 外部时钟怎样变成sys时钟？

```python
self.clock_domains.cd_sys = ClockDomain("sys")
```

在Migen设计里创建名为sys的时钟域，让ClockSignal()/ResetSignal()默认引用它。

```python
self.comb += self.cd_sys.clk.eq(platform.request("clk"))
```

从平台取外部clk端口，直接连到sys时钟。`.eq`建立硬件连线，不是在Python运行时每秒给它赋值。

```python
self.specials += Instance("reset_sync", ...)
```

在RTL中实例化本地reset_sync.v模块。输入接外部reset_n，输出接sys.rst。这里没有FPGA专用复位原语。

### reset_sync.v逐行看

```verilog
(* async_reg = "true" *) reg [1:0] release_pipe;
```

两级触发器存放复位释放状态。async_reg是给后续工具的意图标记，不是插入了某种模拟防亚稳器件，也不能代替CDC检查。

```verilog
always @(posedge clk or negedge reset_n)
```

时钟上升沿或外部低有效复位下降沿会执行这个过程。

```verilog
if (!reset_n) release_pipe <= 2'b00;
```

reset_n拉低时，不必等时钟，立即清两级触发器。

```verilog
else release_pipe <= {release_pipe[0], 1'b1};
```

复位释放后，第一个时钟变01，第二个变11。

```verilog
assign reset = ~release_pipe[1];
```

输出取最高位的反值，所以依次是1、1、0：异步置位，第二个时钟后同步释放。CPU自己的复位采样还会在随后时钟执行；不能把输出变0和“第一条指令已经执行”视为同时发生。

## 3. Wishbone接口怎样接到本地Verilog？

```python
self.bus = b = wishbone.Interface(
    data_width=32, address_width=32, addressing="word")
```

创建adr、dat_w/r、sel、cyc、stb、we、ack、err等信号。这组信号本身不实现存储或应答。

```python
i_cyc=b.cyc, i_stb=b.stb, i_we=b.we, i_sel=b.sel,
i_adr=b.adr, i_dat_w=b.dat_w, o_dat_r=b.dat_r, o_ack=b.ack
```

Instance参数前缀i_/o_表示连到Verilog实例的输入/输出。例如`i_adr=b.adr`最终产生`.adr(某条地址线)`。请求从互连到外设，数据和ACK从外设返回。

```python
self.bus.add_slave("registers", self.registers.bus,
    SoCRegion(origin=0x80000000, size=64, cached=False))
```

让总线管理器把这个接口登记在64字节的地址窗口。没有因此分配64字节RAM；窗口内部由peripheral.v决定如何解释地址。

全局字节地址`0x80000014`经32位word寻址变成Wishbone adr=`0x20000005`。外设取`adr[3:0]`得到5，选择Timer pending。这里利用基址按64字节对齐；若改成任意不对齐基址，必须重新处理译码，不能机械沿用低四位。

## 4. 这次ACK怎么做？

```verilog
reg response_ready;
wire request = cyc && stb;
assign ack = request && response_ready;
```

request说明当前有有效请求。ACK必须同时受request限制，不能在请求撤销后仍给共享应答汇合网络贡献一个高电平。

```verilog
response_ready <= request && !response_ready;
```

请求开始后打一拍，才允许应答。持续请求时交替应答/等待，本模型是小型教学端点，不追求每拍一笔吞吐。

```verilog
wire write = request && ack && we && sel == 4'hf;
```

在实际完成的写事务上更新寄存器。sel必须为1111：本地外设只接受整32位业务写，部分写被应答但不改变寄存器。RAM则另外支持真正的四路字节写使能。20章的形式属性会检查这种行为。

所有请求字段应在等待期间保持稳定；测试平台不能每拍换地址却把它当作同一笔Classic事务。Timer清除用W1C，UART忙时忽略新的发送写，这些都属于本端点的具体协议，需要固件遵守。

## 5. GPIO输入、UART、Timer各是什么电路？

GPIO输入经过gpio_meta→gpio_sync两个同域触发器，降低异步输入传播亚稳态的风险。四位分别同步只适合相互独立的慢信号；不能据此保证任意四位异步数据是同一个时刻的整体值。

UART写入字符后构造`{停止位1, 8位数据, 起始位0}`，从tx_shift[0]开始输出，每隔UART_DIV个时钟右移。默认DIV=8是为了让仿真较短，不是板卡必须使用的波特率。实际波特率是实际输入时钟/UART_DIV；发送期间tx_bits非零，固件轮询忙标志避免覆盖帧。

Timer load寄存器写入后使能倒计数。计到0时停止并置pending，pending直接成为外部IRQ输入的bit0。CPU进入中断后，固件写pending寄存器的1清源；只关闭CPU使能不能清掉外设里持续为1的pending。

## 6. run.py里最关键的综合命令逐行解释

```text
read_verilog ...        读入生成顶层、CPU、复位、外设
hierarchy -check ...    核对顶层和模块引用，缺失实例会失败
proc                    把always过程变成寄存器、多路选择等内部对象
opt                     消除常量和无用连接
memory_collect          收集存储器，输出清单时还没有抹掉数组身份
memory_map              把所有存储变为触发器/多路选择；ROM常量可以优化
opt                     把固定ROM初值折叠进逻辑
synth ... -flatten      展平并综合为通用门/触发器
 delete t:$scopeinfo    删除调试层级元数据，不是删除业务电路
setattr -unset init ... 去掉寄存器的上电init属性，要求复位/启动真正有效
check -assert           有悬空、多驱动等结构问题则报错
write_verilog ...       输出generic.v
```

`$scopeinfo`是新Yosys为保留层级调试信息输出的元数据；不能把它当成未映射的硬件宏。删除它后，实际硬件单元必须全部成为通用逻辑。

加上--map-cells后还有：

```text
dfflibmap -liberty ...  将触发器映射到ICS55库
abc -liberty ...        将组合逻辑映射到ICS55库
read_liberty -lib ...   读入库单元的端口/方向，供结构检查识别
clean                   清理无用中间连接
check -assert           检查映射网表结构
stat -liberty ...       输出库单元数量、库面积
write_verilog ...       输出mapped.v
```

这里的面积是所选Liberty单元面积之和，不是最终die尺寸；布线、pad ring、供电、时钟树还会增加面积。read_liberty不能省略后仍把未知库端口产生的悬空告警当作真实悬空，也不能通过忽略check退出码来假装通过。

PDK模型仿真使用functional定义，没有SDF回标；因此验证逻辑功能，不包含布局后延迟或工艺角速度保证。
