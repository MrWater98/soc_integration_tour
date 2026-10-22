# 15：从 RTL 到 `.fs`——开源工具怎样把电路放进 FPGA

14 章已经描述好了电路：CPU、ROM、RAM、总线、UART、LED 和按键。但 RTL 里只有逻辑与连接，还没决定用 FPGA 中的哪个逻辑块、哪条线路实现它。

本章完成这件事，最后得到能下载的 `tutorial14.fs`。

```text
14 章的输出
RTL + ROM 初值          CST 引脚约束 + 器件/频率
       │                         │
       ▼                         │
     Yosys                       │
   综合、资源映射                │
       │                         │
       ▼                         ▼
 netlist.json ───────────────→ nextpnr-himbaechel
                              布局、布线、时序检查
                                       │
                                       ▼
                                  routed.json
                                       │
                                       ▼
                             Apicula 的 gowin_pack
                                       │
                                       ▼
                                  tutorial14.fs
                                       │
                              16 章下载到 FPGA
```

先记住工具分工：**Yosys 决定用什么资源，nextpnr 决定放在哪里、怎么连，gowin_pack 把结果编码为 FPGA 配置。** openFPGALoader 在下一章负责下载。

## 1. 综合：`counter + 1` 怎么变成硬件？

RTL 中可以写“每个时钟把计数器加一”。Yosys 读懂这个描述，然后生成：保存数值的触发器、计算下一值的加法逻辑，以及复位和选择逻辑。

```text
RTL 描述                       综合后的资源连接

每拍 count ← count + 1         count 的触发器 ─→ 加法逻辑 ─┐
                                  ▲                     │
                                  └──── 下一拍写回 ─────┘
```

在 FPGA 里，加法逻辑会使用 LUT、进位/ALU 等资源。CPU 的译码、计算和流水线同样要映射到这些资源；ROM/RAM 通常会利用 FPGA 的块存储器，具体映射看报告。

**综合网表**就是“哪些资源实例通过哪些信号相连”的清单。它仍可以保存为 Verilog，也可以保存为 JSON。它与原始 RTL 都是电路描述，但网表已经更接近目标 FPGA 的资源。

本章 Tang 路线实际执行：

```text
synth_gowin -family gw2a -top tutorial14
```

`gw2a` 选择资源系列，`tutorial14` 选择顶层模块。具体器件和封装在 nextpnr 阶段进一步确定。综合脚本只读取清单中角色为 `design` 的 HDL，避免将测试台与理想 PLL 仿真模型放进硬件；rPLL 等硬件原语由工具的技术库处理。

## 2. 布局与布线：为什么综合之后还没结束？

FPGA 内部的资源已经制造好了，分布在固定位置。

- **布局**：把网表中的触发器、逻辑、存储器放到具体资源位置。
- **布线**：选择实际可用的连接，把这些资源连起来。

```text
同一条逻辑连接：寄存器 A → 运算逻辑 → 寄存器 B

布局方案一：A ── 运算 ── B        距离短
布局方案二：A ───────── 运算 ───── B   距离长
```

两种方案功能可以相同，线路延迟却可能不同。资源数量放得下，也可能因为位置或连线限制而布不出来；布线成功之后，还要看速度是否满足要求。

`nextpnr-himbaechel` 读取 `netlist.json`，结合具体 FPGA、封装、CST 和时钟目标完成这些工作。本项目使用的具体器件是 `GW2A-LV18PG256C8/I7`，数据库系列名为 `GW2A-18C`。这两个值来自板卡与工具对器件的定义，不能用商品名“20K”代替。

## 3. 时序：为什么要看 Fmax？

以两个寄存器之间的一条路径为例：

```text
时钟边沿 ①                                    时钟边沿 ②
     │                                             │
     ├─ A 输出 → 组合逻辑 → 连线 → 到达 B 的输入 ───┤
     │                                             │
     └────────── 一个系统时钟周期 ──────────────────┘
```

数据需要在 B 下一次采样之前到达，并满足触发器的建立时间。nextpnr 根据映射资源和实际布线估算路径延迟，检查当前时钟目标。

| 系统频率 | 一个周期 | 直观含义 |
|---|---:|---|
| 27 MHz | 约 37.04 ns | 每拍留给数据传播的时间较长 |
| 54 MHz | 约 18.52 ns | 每拍时间减半 |
| 120 MHz | 约 8.33 ns | 对路径延迟要求更紧 |

这些频率是实验目标。**PLL 负责产生频率，时序工具负责检查电路能不能跟上。** PLL 能求出 120 MHz 参数，不保证 CPU 的每条路径都满足 120 MHz。

### Fmax 和实际运行频率有什么区别？

- **实际系统频率**由 14 章的 PLL 配置决定，例如 54 MHz。
- **Fmax** 是工具根据当前布局估计的时序上限，例如某次 54 MHz 构建报告约 108.27 MHz。

这个例子说明工具估计的上限高于 54 MHz；下载后电路仍按 PLL 配置运行在 54 MHz，不会自动跑到 108.27 MHz。

改变目标频率会改变 PLL 参数、部分计数/串口逻辑，并影响布局布线。即使功能相近，工具找到的布局也可能不同，所以 Fmax 不一定随目标频率单调增加。判断时应打开**对应那次构建**的最终报告，不能混用其他目录的数字。

本章脚本没有使用 `--timing-allow-fail`，并检查报告中的 CPU 时钟路径是否存在、是否满足目标。它还把参考时钟与系统时钟中的较大值作为 `--freq` 传入；更复杂的多时钟设计需要为各时钟及跨域路径分别制定约束。

## 4. Apicula 做什么？`.fs` 是怎样出现的？

布局布线结果知道“哪些资源被使用、线路怎么接、PLL 怎么配置”。FPGA 配置入口需要的是芯片能识别的配置数据。

Apicula 提供高云 FPGA 的配置数据库与相关开源工具。本章用其中的 `gowin_pack`，把 `routed.json` 编码为 `.fs`：

```text
routed.json：电路已经映射到具体资源与线路
                  │ gowin_pack
                  ▼
tutorial14.fs：FPGA 配置入口可读取的数据
```

`.fs` 是这条高云工具链的 bitstream 文件格式。本教程的文件大小约为 7.26 MB，这是生成结果的文件长度，不能用来判断 C 程序占了多少 RAM。

### `.fs` 和 C 程序是什么关系？

```text
C / startup.S → GCC → 程序机器码 → ROM 初值 ──┐
                                            │
SoC RTL + FPGA 约束 ─────────────────────────┤
                                            ▼
                                   构建 → tutorial14.fs
```

这份配置既实现 CPU 电路，也携带本方案 ROM 的初始程序。改 `main_tang.c` 后，需要重新编译 ROM 并重新构建 `.fs`，再下载才能看到新行为。

A13/C13 是本章 LED 使用的脚，同时复用 READY/DONE 状态功能，所以打包显式使用 `--ready_as_gpio --done_as_gpio`。否则用户逻辑与配置脚用途不一致，可能出现“设计里有 LED 输出，板上的灯却不受它控制”的情况。

## 5. 按顺序执行三个命令

在教程根目录，先加载本项目已经安装的工具路径：

```bash
source chapters/15-fpga-build/tools.sh
command -v yosys nextpnr-himbaechel gowin_pack openFPGALoader
```

`tools.sh` 调整当前 shell 的 PATH，让后面的脚本找到这些工具；它不把 FPGA 设计下载到板子。本项目固定的 OSS CAD Suite 发布包版本和哈希保存在 `tools-lock.json`，安装目录为 `external/fpga-tools/oss-cad-suite/`。

然后执行：

```bash
# ① 生成带固件的 RTL、初值和板卡约束
python chapters/14-fpga-platform/tang_run.py

# ② 综合成高云资源网表
python chapters/15-fpga-build/run.py --family gw2a \
  --input results/14-tang20k/rtl --output results/15-tang20k

# ③ 布局布线、检查时序、打包 .fs
python chapters/15-fpga-build/build_tang.py
```

综合入口默认使用 `gw2a` 与 Tang 输入目录；命令中显式写出它们，便于核对这一套输入。

| 步骤 | 主要输入 | 主要输出 |
|---|---|---|
| ① 生成 | Python 配置、启动代码与 C | `results/14-tang20k/` |
| ② 综合 | 上一步 `rtl/` 与 ROM 初值 | `results/15-tang20k/netlist.json` |
| ③ 实现与打包 | 网表、同一版本的 CST/参数 | `results/15-tang20k-build/tutorial14.fs` |

脚本会比较综合输入和平台输出的源文件哈希，避免拿旧 ROM 的网表配上新配置。

### 例如：完整构建一个 54 MHz 版本

```bash
python chapters/14-fpga-platform/tang_run.py \
  --sys-clk-hz 54000000 --output results/14-tang20k-54mhz

python chapters/15-fpga-build/run.py --family gw2a \
  --input results/14-tang20k-54mhz/rtl --output results/15-tang20k-54mhz

python chapters/15-fpga-build/build_tang.py \
  --platform results/14-tang20k-54mhz \
  --synthesis results/15-tang20k-54mhz \
  --output results/15-tang20k-build-54mhz
```

三个目录配套使用。当前已有这些结果时，阅读它们即可，无需为了理解教程重新构建。

## 6. 报告打开后看什么？

### 综合结果：电路用了哪些类型的资源？

打开 `results/15-tang20k/REPORT.md` 或 `summary.json`。

| 资源 | 作用 |
|---|---|
| LUT | 实现逻辑函数，例如比较和选择 |
| DFF | 保存一位状态，组成寄存器 |
| ALU / 进位资源 | 加法、减法与计数等 |
| BSRAM | FPGA 的块存储器，承载部分 ROM/RAM |
| MULT18X18 | 专用乘法资源 |
| rPLL | 硬件时钟生成模块 |

综合网表中的单元数量与最终占用的 LUT 数量是不同统计。不要把所有单元相加就称为“用了多少 LUT”。

### 布局布线结果：放得下、跑得动吗？

打开 `results/15-tang20k-build/REPORT.md` 与 `summary.json`：

- `report.utilization`：各资源实际使用量与可用量。
- `report.fmax`：本次时钟路径的目标频率与估计上限。
- `nextpnr.log`：完整过程、关键路径与警告。
- `commands.json`：实际执行的 nextpnr 和打包命令。
- `bitstream_sha256`：本次 `.fs` 的哈希，便于确认下载的是哪一份。

默认 27 MHz 的历史构建使用 4,547/20,736 LUT4、1,688/15,552 DFF、24/46 BSRAM、4/48 MULT18X18，时序目标通过。这些是那次参数与布局的结果；修改存储容量、CPU 或频率后，要看新报告。

比如 LUT 剩余很多、BSRAM 已用一半，扩大 RAM 仍可能先耗尽存储资源。双核是否放得下，也需要实际构建对应配置。

## 7. 哪一步失败，就先读哪份日志

| 现象 | 先看哪里 | 通常要核对什么 |
|---|---|---|
| 找不到工具 | `command -v` 输出 | PATH、工具是否已安装 |
| 综合失败 | `synthesis.log` | 源文件是否齐全、顶层是否正确、原语是否支持 |
| 配置/源码哈希不一致 | 脚本错误与输入目录 | 是否混用了两个版本的生成结果 |
| 布局布线失败 | `nextpnr.log` | 器件、引脚、资源与连线限制 |
| 时序失败 | 最终时序报告 | 哪条路径太慢，当前目标是否可行 |
| 打包失败 | `pack.log` | 系列数据库、原语或配置选项 |

不要因为最终目录存在就认为构建通过；看当前 `summary.json` 和对应日志。

## 本章结束时，板子运行了吗？

本章成功意味着：**电路完成资源映射和布局布线，满足本次工具检查的时序目标，并生成 `.fs`。** 板子还需要 16 章的下载和实物观察。

时序报告是模型估计；真实供电、PLL、IO 与 CPU 启动由上板继续验证。当前 27/54 MHz SoC 已有实物启动记录；120 MHz 有构建结果，没有同等的上板运行结论。
