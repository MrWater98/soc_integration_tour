# 14.3：结果目录里每个文件怎样来的，怎样读？

本篇围绕默认 [results/14-tang20k](../../../../results/14-tang20k/README.md)。下面的路径按仓库根目录计算。

## 1. 先确定你打开的是哪块板、哪个配置

| 目录 | 来源与用途 |
| --- | --- |
| `results/14-tang20k` | 默认 Tang，27 MHz |
| `results/14-tang20k-parameters` | Tang 参数变化实验，准确值读 manifest |
| `results/14-tang20k-54mhz` | Tang 54 MHz 的独立硬件/固件结果 |
| `results/14-tang20k-120mhz` | Tang 120 MHz 的构建输入；不能仅凭目录名认为已上板 |

目录名是运行器的输出选择，不会驱动实际时钟。应查看 `manifest.json` 的 `config.sys_clk_hz`、PLL 配置，以及对应固件头文件。

## 2. 目录分为四层

```text
results/14-tang20k/
├── README.md                 本目录阅读入口
├── manifest.json             器件、配置、PLL、引脚、源文件哈希
├── summary.json              生成和检查的结果
├── digital-summary.json      完整数字仿真结果（执行 sim_tang.py 后）
├── REPORT.md                 运行器写出的说明
├── pin_map.csv               对应球位和 IO 电平
├── builder/
│   ├── csr.csv / csr.json     LiteX 的外设与内存地址图
│   ├── software/include/generated/
│   │   ├── csr.h             外设寄存器访问函数
│   │   ├── soc.h             时钟、CPU、CSR 等配置宏
│   │   └── mem.h             内存地址与容量宏
│   └── gateware/             原始顶层 RTL、初值、CST、构建脚本
├── firmware/
│   ├── linker.ld             本章生成的链接布局
│   ├── test_config.h         本章软件参数，如 LED_MASK
│   ├── program.elf           交叉编译结果
│   ├── program.bin           原始镜像
│   ├── program.map           链接布局与符号
│   └── compile-command.json  完整 GCC 命令
├── rtl/                      教程收集的完整 HDL 与初值快照
└── constraints/              便于下一章使用的 CST/可用 SDC 副本
```

`builder/`、`firmware/` 的许多文件是本地构建产物，没有都纳入 Git。克隆后缺少它们时，先运行 `tang_run.py` 重新生成。已保存的完整 RTL 快照可以独立查看；不能要求已跟踪的目录树包含所有临时工具输出。

## 3. `manifest.json` 是身份卡，不是执行日志

默认配置记录了器件 `GW2A-LV18PG256C8/I7`、family `GW2A-18C`、27 MHz 系统时钟、8 KiB ROM、16 KiB 主 RAM 等。

`firmware_sha256` 标识原始固件镜像。每个源文件还有来源与两个哈希：

- `source_sha256`：原始文件内容。
- `snapshot_sha256`：收集到 `rtl/` 后的内容。

收集器会移除每行末尾空白，并统一末尾换行，所以两个哈希可能不同；应按相应字段核对，不能把不同当成电路被修改的证据。

旧 manifest 的 `board_revision` 仍可能写 `awaiting delivery`。这是生成时的历史注释，不是实时硬件探测，也不是 PCB 版本已确认的证据。实际板卡已到货，实物结果在第 16、17 章记录。

## 4. `summary.json` 的 PASS 各指哪一层？

| 字段 | 实际检查 |
| --- | --- |
| `rtl_generation` | Python/LiteX 完成 RTL 生成 |
| `pin_audit` | CST 资源名、球位、电平与本章核对表一致 |
| `rtl_elaboration` | Icarus 能展开顶层与模块连接 |
| `clock_target` | PLL 参数能得到目标频率，构建脚本含目标频率 |
| `memory_map` | 生成地址图与本章约定一致 |
| `logic` | 心跳与输入同步器的局部 Migen 仿真 |
| `negative_checks` | 故意制造的约束错误被检查器捕获 |

这些检查没有执行 nextpnr 布局布线；`clock_target=PASS` 不能解释为时序已经收敛。

历史 `onboard='SKIP: board not delivered'` 只说明这个生成步骤当时未上板。当前脚本已改为明确记录“生成步骤不访问硬件”，但它不会回写历史结果，也不会查询第 16、17 章的报告。因此读取最新项目进度应看对应实物记录，而不是把一个旧字段当全项目状态。

## 5. 局部逻辑仿真里为什么半周期只有 4？

`check_logic()` 为了很快观察多次翻转，把 `Heartbeat` 的测试半周期设为 4，而非板上的默认 13500000。

```text
测试设置：每 4 拍翻转 → 查看样本 4、8、12、16
板上设置：每 13500000 拍翻转 → 27 MHz 时完整亮灭约 1 秒
```

这个仿真检查计数边界和翻转间隔，并没有测板上灯的一秒周期。按钮局部仿真使用两位信号，是用来验证辅助模块的同步行为；本次 Tang 实物按钮通路是一位。

## 6. 完整 RTL 快照中为什么不止一个 `.v`？

| 文件 | 对应作用 |
| --- | --- |
| `tutorial14.v` | LiteX 生成的顶层：总线、存储、CSR、UART、CRG、GPIO 等 |
| `VexRiscv.v` | CPU 核心本体，来源于 CPU 数据包；不是 Builder 从 C 编译出来的 |
| `tutorial14_rom.init` | 启动代码、C 指令与常量的 ROM 初值 |
| `tutorial14_sram.init` / `tutorial14_main_ram.init` | 对应两块 RAM 的初值输入 |
| `tutorial14_mem.init` | 当前生成 Identifier 存储的初值；结合顶层 Memory 使用点确认 |
| `gowin_primitives.v` | 原语接口/部分逻辑模型，供展开检查用 |
| `gowin_sim_primitives.v` | 数字仿真使用的模型，含理想 PLL 替代 |
| `tang_tb.sv` | 时钟、按钮激励和 UART 解码测试台 |
| `YOSYS_COPYING` | 提取原语模型对应的许可说明 |
| `sources.json` | 快照文件来源、用途、哈希清单 |
| `files.f` / `files_sim.f` | 不同用途的 HDL 文件列表 |

空 RAM 初值文件不意味着已经定义了 C 的 `.bss` 语义。启动代码仍负责清零；也不能依赖未初始化区域“碰巧为零”。

RTL 通过 `$readmemh("tutorial14_rom.init", rom)` 读初值。运行工具时工作目录应使这些相对路径可见，因此脚本在 `rtl/` 中执行相关检查。

## 7. 怎样在顶层找到 Python 对应的电路？

从以下锚点读，不必逐行读完几千行自动命名：

```bash
rg -n 'module tutorial14|Hierarchy|VexRiscv|rPLL|readmemh' \
  results/14-tang20k/rtl/tutorial14.v
rg -n 'assign led|csrbank|input_w|output_r|gw2apll' \
  results/14-tang20k/rtl/tutorial14.v
```

### 第一步：看端口

顶层实际导出 `clk27`、`btn_n0`、`btn_n1`、`led4`、`led5`、`serial_rx`、`serial_tx`。CPU 的 Wishbone 信号都在 FPGA 内部，不是封装上的每根引脚。

### 第二步：看层级注释

`Hierarchy` 中能看到：

```text
cpu、rom、sram、main_ram
uart：FIFO + phy + EventManager
crg：GW2APLL / rPLL
heartbeat、leds、buttons
csr_bridge：Wishbone2CSR
csr_bankarray：寄存器 bank 与 Identifier 存储
```

这份代码通常把很多小模块展开为顶层的组合逻辑、寄存器和 always 块。层级注释中有 `LEDOutput`，不代表最终一定存在一个名为 `LEDOutput` 的独立 Verilog module。

### 第三步：找 CPU 实例

`VexRiscv` 实例的 `iBusWishbone_*` 是取指主接口，`dBusWishbone_*` 是数据访问主接口。它们接到 LiteX 生成的内部信号，再进入共享总线。

单核仍有多个总线主接口，所以会有仲裁器。译码器根据地址选择 ROM、RAM 或 CSR 桥。`ack/dat_r` 再返回当前请求的 CPU 接口。

### 第四步：找 GPIO 地址译码

当前生成结果中，按钮是 `csrbank_0`，LED 是 `csrbank_1`，UART 是 `csrbank_2`。**自动对象后缀 0、1、2 不等于 csr_map 的位置**：构造/收集顺序与地址槽位不是一回事。

按钮 bank 的内部条件可见 `bank_bus_adr[13:9] == 2`，LED 则比较 1。这里已经是按字寻址的 CSR 总线：每个槽位 512 个 32 位访问位置，等于 `512 × 4 = 0x800` 字节。

同时 `assign led5 = ~boardsoc1` 把内部逻辑值取反到外部 LED。名字 `boardsoc1` 是这次生成器的命名，后续可能改变；应按连接关系辨认。

### 第五步：找 PLL 与存储

顶层包含 `rPLL #(...)`。配置参数是 FPGA 硬宏的参数，CPU 无须每次启动用 C 手工配置 PLL。

顶层的 `reg [...] rom [...]` 等是综合前的存储描述。Yosys 后续才根据器件资源映射；本章的 `SRAM` 名称是 LiteX 的 Memory/Wishbone 包装，不是调用一颗 ASIC SRAM 宏。

## 8. CST 来自哪里？

平台资源的引脚约束由原生平台输出，再复制到 `constraints/tutorial14.cst`。例如：

```text
IO_LOC "serial_tx" M11;
IO_PORT "serial_tx" IO_TYPE=LVCMOS33;
IO_LOC "btn_n1" T3;
IO_PORT "btn_n1" IO_TYPE=LVCMOS15;
```

`IO_LOC` 决定顶层端口落在哪个封装球位。`IO_TYPE` 选择该 IO 的电气标准；它没有把板上一个 1.5 V 电源变成 3.3 V。当前按钮1与另几个信号电平不同，不能全文件统一替换。

`audit_cst()` 用本章独立列出的 `PINS` 逐项核对，拒绝：端口集合变化、球位复用冲突、球位错误、电平错误。这个检查也依赖所选平台/参考事实正确，不能代替接线资料审核。

负例主动把 TX 球位改成 RX 球位，检查器报重复；把某条 `LVCMOS33` 改成 `LVCMOS18`，检查器报错。错误只在传入检查器的文本副本中，不会拿去配置板子。

## 9. 为什么有时找不到 `.sdc`？

原生 Apicula 路径不一定生成单独 SDC。本章若找到它才复制；同时检查生成的 `build_tutorial14.sh` 是否带正确的 nextpnr `--freq`。

实际阶段的时序结论要看第 15 章 nextpnr 报告。缺少本章的 SDC 文件，不等于脚本已经检查了所有时序关系，也不等于后续必然没有时钟目标。

## 10. 数字仿真怎样观察 UART，而不是直接看软件变量？

`tang_tb.sv` 产生默认 27 MHz 时钟，把串口 RX 保持高电平。它在 TX 下降沿检测起始位，再按 115200 的位周期采样八个数据位，检查停止位，拼出字符串。

```text
真实 CPU 指令 → 真实 CSR 写入 → 真实 UART FIFO/发送逻辑
                                          ↓
                                      serial_tx
                                          ↓
                              测试台按位采样，重建字符
```

随后测试台按下按钮1，要求读到 `BUTTONS=...1` 且 LED5 低电平；松开要求状态回零、LED5 高电平；按按钮0复位，要求再次 HELLO。还有 50 ms 仿真超时。

`gowin_sim_primitives.v` 里的 PLL 是理想替代，不能验证真实 PLL 的模拟锁定、电压或抖动。当前这份测试台/脚本只接受默认 27 MHz、115200 配置，不能直接拿去认证 54/120 MHz。

## 11. 最后把结果交给谁？

```text
本章 rtl/ + ROM 初值 + CST + manifest
                  ↓
15：Yosys 综合 → nextpnr 布局布线/时序 → Apicula 打包 .fs
                  ↓
16：JTAG 配置 FPGA → 观察 UART、按钮、LED
```

打开本章结果时，应依次问：身份与配置是什么？软件地址是否匹配？ROM 有什么？引脚如何落地？通过的是哪一层检查？这比仅看 `status=PASS` 更能解释整个运行过程。
