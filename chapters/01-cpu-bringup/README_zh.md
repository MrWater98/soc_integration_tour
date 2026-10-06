# 01 —— VexRiscv 能取指并写数据吗？

这是第一个 CPU 级实验。使用 LiteX 原生 VexRiscv 封装、64 字节初始化 ROM 和一个内存映射写入端点。程序尽量短，方便直接从日志理解发生了什么。

```asm
addi x1, x0, 64   # x1 = 0x40
sw   x1, 0(x1)    # 向字节地址 0x40 写入 0x40
```

## 先沿着总线看懂 LiteX

下面按本章生成的 [`sim.v`](../../results/01/rtl/sim.v) 画实际连接。先抓住一条主线：CPU 提出读写请求，仲裁器选择发起者，译码器按地址选择设备，设备返回数据和应答。所有地址范围均为**字节地址**。

```text
                       VexRiscv / minimal
                      ┌────────┴────────┐
                      │                 │
                 iBus：取指        dBus：load/store
                 interface0        interface1
                      │                 │
                      └────────┬────────┘
                               ▼
                    Arbiter + RoundRobin
                  选择一个 master，保持当前事务
                               │
                               ▼
                       共享 Wishbone
                adr / dat_w / sel / we / cyc / stb
                               │
                               ▼
                         Decoder
                        按地址选设备
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
           ROM             WriteTarget       Wishbone2CSR
       0x00–0x3f           0x40–0x7f       0xf0000000–0xf000ffff
       返回机器码          检查完成写入           │ FSM
            │                  │                  ▼
            │                  │               CSR 接口
            │                  │            本章没有 CSR 寄存器组
            └──────────────────┼──────────────────┘
                               ▼
                  返回选择：dat_r / ack / err
                               │
                 ACK/ERR 只送给当前获准的 master
                               ▼
                              CPU

Timeout 并行观察共享总线：cyc & stb 有效却一直没有 ACK
CRG 提供 sys 时钟与复位，供 CPU、互连、ROM、端点和桥使用
本章 CPU externalInterruptArray = 0，没有外设中断源
```

图中的 `interface0/1` 是 **CPU Wishbone 信号名的尾部编号**；CSR 桥附近也有名为 `interface0/1` 的另一组信号，读 RTL 时要带上完整前缀。本章 ROM 在树里显示为 `SRAM`，因为 LiteX 用同一个存储器包装类构造只读 ROM；本章没有可写 SRAM。

### 管理对象怎样变成这些连接？

`sim.v` 开头的树是模块层次图。`bus`、`csr`、`irq` 是 SoC 下的同级对象；缩进表达归属，信号连线由生成的 RTL 决定。

| 名字 | 构建时负责什么 | 本章运行时对应什么 |
| --- | --- | --- |
| `bus / SoCBusHandler` | 登记 CPU master、设备 slave 和地址区域 | 生成仲裁、地址译码、响应选择与超时逻辑。 |
| `csr / SoCCSRHandler` | 分配 CSR 页和寄存器区域，登记 CSR 接口 | 本章保留 CSR 桥，但没有 GPIO、Timer 等 CSR 设备。 |
| `irq / SoCIRQHandler` | 分配外设中断源编号 | 本章无中断源，CPU 的 32 位外部中断输入保持为 0。 |
| `write_target / WriteTarget` | 加入我们定义的 Wishbone 从设备 | 检查地址、写入值和 `sel`，产生 ACK，并打印仿真完成标记。 |
| `csr_bridge / Wishbone2CSR` | 把 CSR 区域接到 Wishbone | FSM 将 Wishbone 访问变成 CSR 的地址、读写使能和数据，再返回应答。 |
| `csr_bankarray / CSRBankArray` | 收集外设 CSR，生成寄存器组 | 本章集合为空；加入 CSR 外设后再生成对应寄存器组及互连。 |
| `crg / CRG` | 建立时钟和复位域 | 驱动硬件的时钟与复位信号。 |

后面章节里的 `registers / RegisterSlave` 与本章 `write_target` 位于同一种位置：它们直接接 Wishbone。`RegisterSlave` 保存写入值并支持读回；本章 `WriteTarget` 只观察完成写入，读数据固定为 0。这些都是外设端点，不是 CPU 的 `x0–x31` 寄存器。

### 一次请求发出去，又怎样回来？

```text
取指：iBus 发出地址 0 的读请求
      → 仲裁选中 iBus → 译码选中 ROM
      → ROM 返回机器码和 ACK → ACK 送回 iBus
      → CPU 执行 addi，得到 x1=0x40

写入：CPU 执行 sw，dBus 发出请求
      字节地址=0x40，Wishbone adr=0x10
      dat_w=0x40，we=1，sel=0xf，cyc=stb=1
      → 仲裁选中 dBus → 译码选中 WriteTarget
      → 端点接收并检查写入，更新 ACK
      → 共享响应送回 dBus，CPU 的这笔访问完成
```

在正常实验中，端点接收正确写入时执行 `$display` 和 `$finish`，所以日志证明 CPU 发出了预期 store；仿真会在这个检查点结束，不继续观察 CPU 收到 ACK 后的后续指令。

可以在 RTL 中对照三个位置：

```verilog
// 1. 按字地址译码：0x10 个 32 位字，就是字节地址 0x40。
decoder0[1] = (adr[29:4] == 1'd1);

// 2. 地址、数据等共享；仅命中的设备收到有效 CYC。
assign projectsoc_writetarget_cyc = (cyc & decoder0[1]);

// 3. 汇总 ACK 后，仅返给当前获准的 CPU 接口。
assign projectsoc_vexriscv_interface1_ack =
    (ack & (roundrobin1 == 1'd1));
```

读数据先按所选设备组合到共享 `dat_r`，再送到两个 CPU 接口；只有被授予接口的 ACK 有效，CPU 才接收对应事务的结果。总线承载地址、读写控制和数据；仲裁决定**谁使用**，译码决定**访问谁**，端点决定**何时完成**。

`Timeout` 观察未完成请求。本次 RTL 的等待计数从 `1_000_000` 开始，到零后返回 `ack=1`、`dat_r=0xffffffff` 并置内部超时标记，没有在此处拉高 `err`。因此 ACK 本身不能证明目标设备正确响应。no-ACK 实验在 600 周期结束，早于总线超时，只检查端点缺少 ACK 时请求仍在等待。

以后加入 Timer 时，会出现独立的中断信号路径：

```text
CPU → Wishbone → CSR 桥 → Timer 寄存器：设置计数、使能、清 pending
Timer → IRQ 信号 → CPU：事件发生，请求进入 ISR
```

`irq` 管理器在构建时安排源编号，运行时由硬件信号通知 CPU；ISR 再通过总线访问寄存器处理事件。

## 第一次用 `SoCCore`：这些参数在配置什么？

本章的 `ProjectSoC` 继承 LiteX 的 `SoCCore`。`super().__init__(...)` 让 LiteX 按参数建立 CPU、主总线和集成存储器；之后代码再自己添加 `WriteTarget`，作为 CPU store 的目标。`SoCCore` 不会自动生成这个实验端点。

| 参数 | 本章设置 | 为什么这样设置 |
| --- | --- | --- |
| `platform` | 仿真 `SimPlatform` | 描述仿真时钟/引脚，不是实体开发板；运行器再用 `CRG` 建立 `sys` 时钟域。 |
| `clk_freq` | `1_000_000` | 声明本次仿真的系统时钟，是方便观察的实验设置，不是 VexRiscv 的固定要求。修改时要让 LiteX 声明与仿真时钟保持一致。 |
| `cpu_type` | `"vexriscv"` | 选择 LiteX 原生注册的 VexRiscv CPU 封装。 |
| `cpu_variant` | `"minimal"` | 选择 RV32I、无 I/D cache 的预生成核心。 |
| `cpu_reset_address` | `0` | 设置 CPU 复位向量。LiteX 将值接到预生成 CPU 的 `externalResetVector` 输入，CPU RTL 在复位时使用这个向量。 |
| `integrated_rom_size` | `0x40`（64 字节） | 只给本实验的短指令序列分配最小 ROM。SoCCore 把 ROM 映射到 CPU 的复位地址，也就是 0。 |
| `integrated_rom_init` | 16 个机器码字 | 把 `addi`、`sw`、停机跳转和填充 NOP 放进 ROM；不是告诉 CPU 从哪里复位。 |
| `integrated_sram_size` | `0` | 本章不验证 SRAM，先不创建 SRAM 区域。 |
| `integrated_main_ram_size` | `0` | 程序不使用 C 运行时、栈或可写数据区，所以暂时不需要 main RAM。 |
| `with_uart / with_timer / with_ctrl` | 都为 `False` | 关闭本实验不使用的默认 UART、Timer 和控制模块，让系统只保留当前要观察的路径。 |

`bus_standard` 没有显式传入，因此主总线使用 LiteX 默认的 Wishbone。`bus_arbiter="transaction"` 让仲裁器在 ACK/ERR 到来前保持当前 master，适合同时存在的取指和数据 Wishbone 请求。

### 本章怎样把自定义模块接进 LiteX？

`SoCCore` 创建的是通用 SoC 结构；自定义端点要由项目明确注册。`add_module("write_target", ...)` 把 Migen 模块纳入设计层次，`bus.add_slave(...)` 把它的 Wishbone 接口接到 LiteX 主总线，`SoCRegion(origin=0x40, size=0x40, ...)` 告诉地址译码器它响应哪段地址。`SoCIORegion` 还把这段低地址登记为 CPU 可访问的 I/O 区域。只创建模块而不 `add_slave`，CPU 的总线访问就到不了它。

端点基址 `0x40` 和 `0x40` 字节的区域大小是这个小实验的选择。程序的 `sw` 地址必须落在区域内；改基址或范围时，要同步改指令/数据检查和 `SoCRegion`。同理，64 字节 ROM 来自当前镜像深度，并且必须覆盖地址 0 的复位指令。

## 这些 Python 调用怎样变成 RTL？

Python 在构建阶段描述硬件，不是 CPU 运行时调用的函数。看这段连接：

```python
self.add_module("write_target", WriteTarget())
self.bus.add_slave(
    name="write_target",
    slave=self.write_target.bus,
    region=SoCRegion(origin=0x40, size=0x40, mode="rw", cached=False),
)
```

`WriteTarget()` 创建 Migen 子模块；`self.add_module` 把它放进 SoC 硬件层次。`wishbone.Interface(...)` 创建由 `adr`、`dat_w`、`dat_r`、`sel`、`cyc`、`stb`、`we`、`ack` 等信号组成的接口，但它本身不规定 ACK 怎么产生。`slave=...bus` 把这组信号交给 LiteX 总线管理器。`SoCRegion` 给出译码条件：字节地址从 `0x40` 开始，大小 64 字节，允许读写，并标记为不可缓存。SoC elaboration 阶段，LiteX 根据这些信息生成地址译码、请求分发和读回应答选择逻辑。

接口采用字寻址，所以生成 RTL 中的 Wishbone `adr` 是 30 位字地址；字节地址 `0x40` 对应 `adr=0x10`。生成 RTL 中能找到类似结构（LiteX/Migen 生成的信号名可能随版本改变）：

```verilog
decoder0[1] = (adr[29:4] == 1'd1); // 选中 0x40–0x7f 端点区域
projectsoc_writetarget_cyc = cyc & decoder0[1];
projectsoc_writetarget_adr = adr;
projectsoc_writetarget_dat_w = dat_w;
```

`WriteTarget` 中的 Migen 语句会变成寄存器和组合逻辑：`bus.dat_r.eq(0)`、`bus.err.eq(0)` 对应常量输出；`self.sync` 中的 ACK 逻辑对应时钟沿触发的寄存器更新；Python `If` 条件对应硬件比较器和选择器。CPU 的两个 Wishbone master 由 LiteX 仲裁后进入地址译码器；译码器只把匹配区域的请求送给 slave，slave 的 `ack/dat_r` 沿共享总线返回被授予的 master。

运行 `run.py` 后，两种构建使用的完整 RTL 文件分别保存在 [`results/01/rtl`](../../results/01/rtl) 和 [`results/01-no-ack/rtl`](../../results/01-no-ack/rtl)。每个目录都有 LiteX 顶层 `sim.v`、`VexRiscv_Min.v` CPU 定义、ROM 初始化数据，以及从仿真器实际 Verilog 源清单复制而来的 `rtl_sources.txt`。前者展示正常 ACK 路径，后者展示端点永不应答时的逻辑。重新运行会刷新文件。

这些参数要一起看：CPU 复位向量是 `0`，集成 ROM 也从 `0` 开始，ROM 初始化内容必须对应这个起点；端点从 `0x40` 开始，不能与 ROM 的 `0x00–0x3f` 重叠。`integrated_rom_size` 的单位是字节，而 `integrated_rom_init` 每项是一个 32 位字，本章 16 字正好是 64 字节。若只扩大 ROM 却不移动端点，`0x40` 会被 ROM 占用；若只改 reset address 而不重链或重排 ROM 镜像，CPU 会从错误位置取指。

### 复位时 PC 为什么回到 0？

`cpu_reset_address=0` 是构建配置，不是 Python 在每个时钟周期写 PC。LiteX 调用 CPU 封装的 `set_reset_address(0)`，将常量 0 接到预生成核心的 `externalResetVector` 输入。复位信号作用于 CPU 后，RTL 把 PC 复位为 0；复位释放后，CPU 从地址 0 取指。SoCCore 同时把集成 ROM 映射在 reset address 上，因此地址 0 正好有 ROM 内容。

```text
SoCCore: cpu_reset_address=0
       ├── VexRiscv RTL：复位 PC ← 0
       └── integrated ROM：映射起点 = 0
                              │
复位释放后，CPU 从 0 取指 ────┘
```

复位向量和 ROM 内容必须匹配：PC 从哪里取指，固件就必须放到哪里。这里还没有 ELF 的 `ENTRY` 或 linker script；ROM 由 `integrated_rom_init` 直接初始化。

## 常见问题

### 缓存能选吗？为什么 CPU 有两条总线？

LiteX 的 VexRiscv wrapper 提供多个预生成变体。本章选 `minimal`，省去缓存和 M 扩展，先观察最直接的存储器访问。取指和 load/store 仍然是两个 Wishbone master：取指走 `ibus`，数据读写走 `dbus`。

```text
VexRiscv/minimal
  ibus（取指） ─┐
                ├─ LiteX 事务仲裁器 ─ 地址译码 ─ ROM / SRAM / 外设
  dbus（数据） ─┘
```

| `cpu_variant` | 指令缓存 | 数据缓存 | 主要用途 |
| --- | --- | --- | --- |
| `minimal` | 无 | 无 | RV32I 最小教学配置 |
| `lite` | 有 | 无 | 指令缓存加 RV32IM |
| `standard` | 有 | 有 | 常用通用配置 |
| `linux` | 有 | 有 | Linux 级配置 |

配置来自 LiteX 自带的 VexRiscv RTL 文件；选择不同 variant 会让 LiteX 加入相应 Verilog，并设置编译器 ISA flags。变体名不是资源面积承诺，最终面积还要看综合结果。

为什么指定 `bus_arbiter="transaction"`？`ibus` 会连续取指，`dbus` 也可能同时等待访问。如果按周期轮换 grant，事务中的地址、控制信号和应答可能分属不同 master。事务仲裁会保持当前 master，直到 ACK/ERR 完成；这是本章共享总线需要的协议边界。

### 为什么只用两条指令？

`addi` 产生一个确定的数值，`sw` 把它变成总线上可观察的事务。如果端点收到预期地址和数据，就说明 CPU 已退出复位、取到指令、执行了指令并发出了 store。此时不需要 C 运行库、栈或其他外设来增加干扰。

### 第一次 `FETCH` 能证明指令执行了吗？

它证明复位地址处的一次 ROM 读取完成。VexRiscv 可能预取指令，因此一条 fetch 日志不能证明某条指令已经执行。端点收到 `0x40` 写入是更强的证据：只有程序执行到 `sw` 才会发出这个写操作。

### 为什么 `0x40` 会变成 Wishbone 地址 `0x10`？

固件和 LiteX 地址图使用字节地址。这里的 32 位 Wishbone 端点按字寻址，每个地址单位代表 4 字节，所以字节地址 `0x40` 对应 Wishbone 字地址 `0x40 / 4 = 0x10`。转换的是地址单位，写入的数据仍然是 `0x40`。

### Python 文件里为什么找不到 `Wishbone`？

本章的两个 CPU master 本来就是 Wishbone。`cpu_bus0` 和 `cpu_bus1` 分别接取指与数据端口；LiteX 的 `SoCBusHandler` 负责仲裁、地址译码及应答返回。

### no-ACK 实验具体捕获了什么？

测试配置成不让端点应答 store。CPU 请求因此一直挂起：日志先记录字节地址 `0x40`、数据 `0x40` 的 `DATA_WAIT`，到限定周期后仿真超时。测试通过是因为它抓到了一个一直有效、却没有完成的请求；它不能打印正常写入完成标志。这把“CPU 发起请求”和“目标完成事务”区分开。

## 运行与观察

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

第一个命令分别运行端点正常应答和 ACK 被抑制的真实 CPU 仿真。第二个命令是一个小型时序练习，用来理解请求/应答；它不能替代 CPU 仿真。

查看 `results/01/`、`results/01-no-ack/` 中的构建日志、运行日志、地址图和 VCD 波形。波形里可以依次看复位、取指 `ibus`、数据 `dbus`、共享 Wishbone 请求和端点 `ack`。`cyc`、`stb` 同时有效表示请求有效；只有目标应答时事务才完成。

## PASS 能证明什么？

正常 PASS 表示 VexRiscv 从复位地址取指，并让端点观察到预期写入。`PASS 01-NO-ACK` 表示检查器发现请求没有 ACK；它不代表写入成功。第 02 章会单独验证从设备应答规则，让各种错误更容易定位。
