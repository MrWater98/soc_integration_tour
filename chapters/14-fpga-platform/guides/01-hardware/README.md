# 14.1：Python 怎样构造板上真正运行的电路？

先打开本章的 [tang_soc.py](../../tang_soc.py) 和 [tang_config.py](../../tang_config.py)。本篇沿着构造函数逐步解释。所有数值以默认 Tang 配置为例。

## 1. Python 在哪里执行？

```text
电脑：Python 执行构造函数 → 产生电路描述 → 输出 Verilog
FPGA：Verilog 经综合/布局布线形成电路 → 每个时钟持续工作
CPU：电路中的 VexRiscv 取 ROM 指令 → 执行 C 编译出的程序
```

Python 对象是描述电路的工具。下载完成后，板子上没有 Python 解释器在执行这些语句。

Migen 是独立的硬件描述库，LiteX 使用它来组织 SoC。`Module`、`Signal`、`If` 来自 Migen；`SoCCore`、`Builder`、板卡集成来自 LiteX/LiteX-Boards。`LiteXModule` 在 Migen 模块机制上提供一些便利，例如自动登记子模块和时钟域。

## 2. 谁调用了 `BoardSoC`？

```text
运行 tang_run.py
  └─ generate(result, cfg, words)
       ├─ soc = BoardSoC(cfg, words)
       │    ├─ Platform：器件和板上资源
       │    ├─ SoCCore：CPU/总线/存储/UART
       │    ├─ CRG：时钟、复位
       │    └─ Heartbeat、LEDOutput、ButtonInput
       └─ Builder：生成地址图、头文件、RTL、约束
```

`cfg` 是配置对象，`words` 是要放入 ROM 的 32 位字数组。它们分别决定硬件参数和固件初始内容。

### `cfg` 配置对象到底长什么样？

它是本章自己定义的普通 Python 对象，类型是 [tang_config.py](../../tang_config.py) 中的 `Config`。`cfg` 只是运行器给这个对象起的变量名；它不是 LiteX 预先提供的对象，也不是 FPGA 内部的寄存器。

实际字段定义：

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Config:
    reference_clk_hz: int = 27_000_000
    sys_clk_hz: int = 27_000_000
    baud: int = 115200
    led_count: int = 1
    button_count: int = 1
    blink_hz: int = 1
    rom_size: int = 8192
    sram_size: int = 4096
    main_ram_size: int = 16384
    stack_size: int = 1024
    por_cycles: int = 65536
```

上面展示的是字段部分；真实文件还有 `validate()` 和三个 property，下面继续解释。

`dataclass` 自动提供按字段创建对象、打印对象等代码。`frozen=True` 表示创建后不允许普通字段赋值，避免生成硬件与编译固件之间意外改变配置。

```python
from tang_config import Config

cfg = Config().validate()
print(cfg.sys_clk_hz)     # 27000000
print(cfg.main_ram_size)  # 16384
```

打印整个 `cfg`，可以看到：

```text
Config(reference_clk_hz=27000000, sys_clk_hz=27000000,
       baud=115200, led_count=1, button_count=1, blink_hz=1,
       rom_size=8192, sram_size=4096, main_ram_size=16384,
       stack_size=1024, por_cycles=65536)
```

因此 `cfg.rom_size` 就是在读该对象的 `rom_size` 字段，和读取普通 Python 对象属性一样。

### 哪些字段控制哪里？

| 字段 | 当前默认值 | 使用位置与含义 |
| --- | --- | --- |
| `reference_clk_hz` | 27000000 Hz | `CRG` 声明板上 PLL 输入；当前板卡事实 |
| `sys_clk_hz` | 27000000 Hz | `SoCCore.clk_freq`、PLL 目标、UART/心跳相关计算；可调目标 |
| `baud` | 115200 | UART 波特率，电脑端要匹配 |
| `led_count` | 1 | 固件 `LED_MASK` 的宽度；当前只配置一个 CPU LED，不含独立心跳 LED |
| `button_count` | 1 | 当前板卡配置的输入数量约定，验证器要求为 1 |
| `blink_hz` | 1 Hz | 硬件心跳完整亮灭频率 |
| `rom_size` | 8192 字节 | ROM 电路容量、镜像检查和链接布局 |
| `sram_size` | 4096 字节 | SoCCore 创建的另一块片内 SRAM |
| `main_ram_size` | 16384 字节 | 主 RAM 电路和固件的数据/栈布局 |
| `stack_size` | 1024 字节 | 链接脚本预留的栈预算；不是创建一颗独立栈 RAM |
| `por_cycles` | 65536 拍 | 上电等待计数器，按 27 MHz 参考时钟计数 |

`led_count`、`button_count` 看起来可填数值，但当前 Tang 接线代码明确连接 LED5 和按钮1，`validate()` 也只接受 1。要扩展数量，必须一起扩展平台资源连接、约束审核和固件；不能只把字段改成 4 就认为四个脚已经接好了。

### 命令行怎样把默认值改成 54 MHz？

```bash
python chapters/14-fpga-platform/tang_run.py \
  --sys-clk-hz 54000000 --output results/14-tang20k-54mhz
```

`tang_run.py` 将参数名 `--sys-clk-hz` 转为 Python 名称 `sys_clk_hz`。没有填写的选项是 None，运行器把它们过滤掉，再执行：

```python
cfg = Config(sys_clk_hz=54000000).validate()
```

所以只有系统时钟字段被覆盖，其余沿用默认值；参考输入仍然是板上的 27 MHz。`--output` 选择结果目录，不属于 `Config` 的电路字段。

`validate()` 检查本章的时钟实验范围（当前 10–150 MHz）、IO 数量、容量、栈预算等，成功时返回对象自身；失败时抛出错误。通过这层检查仍不等于 PLL 一定可实现、资源装得下或时序通过，这些需要后面的检查。

### 三个 property 是实际字段吗？

它们是读取时计算出来的属性：

```python
@property
def values(self):
    return asdict(self)

@property
def half_period(self):
    return self.sys_clk_hz // (2 * self.blink_hz)

@property
def regions(self):
    return {
        'rom': (0, self.rom_size),
        'sram': (0x10000000, self.sram_size),
        'main_ram': (0x40000000, self.main_ram_size),
        'csr': (0xf0000000, 65536),
    }
```

- `cfg.values` 把字段转成字典，供 `manifest.json` 记录；这里记录的是输入配置。
- `cfg.half_period` 默认计算出 13500000，供心跳计数器使用；54 MHz 时自动变成 27000000。
- `cfg.regions` 返回本章**预期**地址图，运行器拿它与 Builder 生成的实际地址图比较；这个字典本身不会建立总线从设备。

配置沿这条路径发挥作用：

```text
默认字段 + 命令行覆盖 → Config → validate → cfg
                                           │
                        ┌──────────────────┼──────────────────┐
                        ▼                  ▼                  ▼
                   BoardSoC / CRG      firmware()       manifest / 地图审核
                   构造电路参数        生成软件布局      记录和检查配置
```

`cfg` 到这里仍只是电脑上的 Python 数据。对应字段只有被代码用于实例化电路、生成常量或编译固件后，才会影响最终 FPGA 行为。

Tang 的辅助逻辑现在按职责独立：`firmware.py` 编译固件，`checks.py` 检查局部逻辑，`build_utils.py` 提供路径/JSON/哈希工具，`io_cores.py` 定义 GPIO 与心跳电路。本章只有 Tang 平台的构建入口。

## 3. `Platform` 不会自动生成 CPU

```python
platform = sipeed_tang_primer_20k.Platform(
    dock='standard', toolchain='apicula')
```

这里选择 Tang Primer 20K 的器件、标准 Dock 资源与 Apicula 工具链适配。`Platform` 保存“资源名 → 信号 → 封装球位/电平”的描述。

例如 `platform.request('serial')` 返回带 `tx`、`rx` 成员的一组信号；`platform.request('led', 4)` 返回 LED4 对应的信号。它们接到什么球位，由平台资源表和最终 CST 约束决定。

```text
代码资源 ('led', 4)
       ↓ request
Migen 信号
       ↓ RTL 导出
顶层端口 led4
       ↓ CST：IO_LOC "led4" A13
FPGA 封装 A13
       ↓ 已焊好的电路板连线
Dock LED4
```

LiteX 的 UART 层级中可能出现 `RS232PHY` 名称；本板串口引脚仍按 CST 的 CMOS IO 标准工作，名字不意味着引脚输出传统 RS-232 电压。

资源编号 4 是板卡资源的编号，不是说这个 SoC 必须有四位 GPIO。

## 4. 为什么要配置 READY/DONE 为 GPIO？

```python
for name in list(platform.toolchain.options):
    if name.startswith('use_'):
        platform.toolchain.options[name] = int(
            name in ('use_ready_as_gpio', 'use_done_as_gpio'))
```

当前 LED4/LED5 使用与 READY/DONE 功能相关的引脚。代码把这两项选为 GPIO，其余 `use_*` 选项设为 0，保留本实验的下载等专用通路。

这是配置器件引脚复用方式，不是创建 LED 寄存器。后者由下面的 `LEDOutput` 实现。打包 bitstream 时也需要对应选项，所以第 15 章的打包命令会继续处理它们。

## 5. `super().__init__` 一次建立哪些模块？

`BoardSoC` 继承 `SoCCore`。调用父类构造函数时，LiteX 根据参数实例化并连接基础电路。

| 参数 | 本章值 | 为什么这样写 |
| --- | --- | --- |
| `clk_freq` | 默认 27000000 | 告诉 UART 等电路系统时钟频率；不是直接生成时钟 |
| `cpu_type` / `cpu_variant` | `vexriscv` / `standard` | 选择现有 CPU 集成与匹配的预生成核心 RTL |
| `cpu_reset_address` | 0 | 把 CPU 复位入口放在 ROM 开头 |
| `integrated_rom_size` | 8192 字节 | 在 FPGA 内部创建启动程序存储空间 |
| `integrated_rom_init` | `rom_words` | 把编译后的程序放入该 ROM 初值 |
| `integrated_sram_size` | 4096 字节 | 创建名为 `sram` 的另一片内部 RAM |
| `integrated_main_ram_size` | 16384 字节 | 创建本固件使用的数据/栈 RAM |
| `with_uart` | True | 加入 UART 外设 |
| `uart_name` | `serial` | 请求平台的 `serial` 资源 |
| `uart_baudrate` | 115200 | UART 发送位的速率，电脑端也要匹配 |
| `with_timer` / `with_ctrl` | False / False | 本章用轮询，复位来自按钮/CRG；没有软件复位控制器 |
| `ident` | 一段字符串 | 建立可供软件读取的标识信息，不是启动程序 |

默认大小都来自本章配置。当前 `Config.validate()` 要求存储容量为至少 1024 的二次幂，这是本教程的实现约束，不是所有存储器的通用规则。

## 6. `Signal`、`.eq`、`comb`、`sync` 分别是什么？

```python
heartbeat = Signal()
self.comb += platform.request('led', 4).eq(~heartbeat)
```

- `Signal()` 创建一位信号；`Signal(32)` 创建 32 位信号。
- `.eq(...)` 创建赋值描述，左侧信号由右侧表达式驱动。
- `self.comb +=` 添加组合逻辑，输入改变后输出随组合电路传播。
- `self.sync +=` 添加 `sys` 时钟域的时序逻辑，在时钟边沿更新寄存器。
- `self.sync.por +=` 添加到另一个名为 `por` 的时钟域。
- Migen 的 `If` 描述条件电路；Python 的 `if` 则在生成时选择要创建哪段电路。

因此 `~heartbeat` 生成一个反相关系。代码不会在运行时反复执行 Python 的这行赋值。

## 7. 两条 LED 路径有什么区别？

```text
LED4：sys 时钟 → 计数器 → heartbeat → 反相 → led4
LED5：CPU store → Wishbone → CSR 桥 → output 寄存器 → 反相 → led5
```

`Heartbeat` 每到半周期末尾，将计数器归零并翻转输出。默认：

```text
sys = 27000000 Hz，blink_hz = 1
half_period = 27000000 / (2 × 1) = 13500000 个周期
每 0.5 秒翻转一次，完整亮灭周期为 1 秒
```

因 LED 低电平点亮，输出前取反。LED4 闪烁证明计数器那条电路在工作；它不要求 CPU 已经执行到 `main()`。

LED5 的逻辑信号只有一位，来自 `LEDOutput`：

```python
self.output = CSRStorage(len(pins), name='output')
self.comb += pins.eq(self.output.storage)
```

CPU 写寄存器后，存储的位保持下来，持续驱动输出。CPU 不必不停重发“保持亮”的命令。本固件循环写是为了不断跟随按钮状态。

## 8. 按键为什么经过同步器？

```python
self.add_module('buttons', ButtonInput(
    ~platform.request('btn_n', 1)))
```

按钮低电平表示按下，取反后软件得到“按下=1”。`ButtonInput` 内部：

```python
synced = Signal(len(pins))
self.input = CSRStatus(len(pins), name='input')
self.specials += MultiReg(pins, synced, n=2)
self.comb += self.input.status.eq(synced)
```

```text
外部按键 → 取反 → 第一级采样寄存器 → 第二级采样寄存器 → CSRStatus → CPU
```

外部按钮变化不与 `sys` 时钟同步，两级同步降低亚稳态传播风险。它不是机械按键消抖器，按一次可能出现多次状态变化。多位总线也不能仅靠逐位同步就保证同时采样一致。

本章宽度是一位，由传入的信号决定。`CSRStatus` 表示状态来自硬件；软件读地址不会改变按钮本身。

## 9. CRG：系统时钟为什么不能直接靠一个数字产生？

```python
self.cd_por = ClockDomain('por', reset_less=True)
self.cd_sys = ClockDomain('sys')
```

时钟域是一组“用哪个时钟、用哪个复位”的电路约定。`por` 使用板上 27 MHz 输入，负责上电等待；`sys` 使用 PLL 输出，驱动 CPU、UART、总线等。

```text
clk27 ───┬─→ por 计数器 ─→ PLL reset ─┐
         │                            │
         └─→ rPLL ── sys 时钟 ────────┼─→ CPU/总线/外设
                └─ locked ─→ 复位同步器┘
btn_n0 ─→ 重装 por 计数器，同时请求 PLL reset
```

`reset_less=True` 表示 `por` 域不使用普通域复位来清这个计数器。本实现依赖 FPGA 的寄存器配置初值，计数器初始为 `por_cycles`。按住按钮也会不断重装它。

默认等待 65536 个参考时钟，约 `65536 / 27000000 = 2.43 ms`，然后才能释放 PLL reset。这个数是本章配置，PLL 锁定还需要自己的时间。

## 10. PLL 的三个调用各做什么？

```python
pll.register_clkin(clk, cfg.reference_clk_hz)
pll.create_clkout(self.cd_sys, cfg.sys_clk_hz,
                 margin=0, with_reset=False)
self.specials += AsyncResetSynchronizer(
    self.cd_sys, pll.reset | ~pll.locked)
```

1. `register_clkin` 声明输入信号和频率。
2. `create_clkout` 选择分频组合，将输出接到 `sys`。`margin=0` 要求精确目标，能否实现还取决于 PLL 的合法配置。
3. `with_reset=False` 让这个调用不自动提供系统复位；下一行显式处理它。
4. `pll.reset | ~pll.locked` 表示 PLL 还在复位或没锁定时，系统保持复位。
5. `AsyncResetSynchronizer` 提供异步置位、同步释放复位的实现。

默认 27 MHz 也使用 PLL。生成 RTL 中可找到 `rPLL` 实例，不是因为输入与输出同频就自动绕过它。

当前 `manifest.json` 的默认配置是 `idiv=1`、`fdiv=1`、`odiv=32`、VCO=864 MHz。生成的 `IDIV_SEL=0`、`FBDIV_SEL=0` 是原语的编码：数值 0 表示除数/反馈倍数 1。不能把编码 0 理解为“除以零”。

改成 54 MHz 时，`clk_freq`、PLL 输出、UART 分频和心跳周期必须使用同一配置重新生成。仅手改头文件不会改变 FPGA 的真实时钟。

## 11. 复位 PC=0 的联系在哪里？

```text
CPU 参数 cpu_reset_address=0
           ↓ LiteX 的 VexRiscv 集成
核心实例的复位入口输入
           ↓ 系统复位释放
CPU 从字节地址 0 取指
           ↓ 总线译码
ROM[0]，其内容来自 startup.S 编译结果
```

复位逻辑负责“什么时候开始”，CPU 复位入口参数负责“从哪里开始”，ROM 初值负责“开始执行什么”。三者需要一起正确。

最后，`Config.validate()`、PLL 参数计算、CST 检查、数字仿真和板上运行分别检查不同环节。阅读下一篇时，会看到软件怎样使用这套电路。
