# 文件是怎样产生的？从 LiteX 定义到 results 产物

这是一份贯穿教程的文件说明。第 06 章第一次系统使用 `SoCCore/Builder` 时阅读，之后遇到陌生结果文件可以回来查。

读一个文件，先问三件事：**谁写出它？写它时用了什么输入？后面的哪一步要读它？** 文件名相同，不代表不同章节的生产方式相同。

## 1. results 是目录约定，不是一款工具

```text
我们的运行器选择 results/章节号
             │
             ├─ 调用 LiteX：生成电路、地址、头文件、构建工程
             ├─ 调用 GCC/链接器：编译 CPU 固件
             ├─ 调用 Verilator/C++：编译电脑上的仿真器
             ├─ 调用 FPGA 工具：综合、布局布线、打包
             └─ 自己写：配置、快照清单、日志、报告、检查结果
```

所以并非 `results/` 中所有文件都由 LiteX 生成。LiteX 也不自动知道教程的章节编号：`output_dir` 和各输出路径由我们的 Python 运行器指定。

`build_and_run()`、`build_program()`、`firmware()` 是本教程的辅助函数；`Builder`、`SoCCore`、`CSRStorage` 等才是 LiteX API。各章节的逻辑辅助文件保留在本章目录，本文不构成运行时依赖。

## 2. 本教程有几种生成方式？

| 章节/路径 | 实际机制 | 不应误解成什么 |
| --- | --- | --- |
| 01 | 从 CPU 数据包取真实 RTL，与本章手写测试台交给 Verilator | 不是 Builder 自动生成整套 SoC |
| 02 | Migen/LiteX Wishbone 元件的局部验证，入口 `verify.py` | 不要求有 CPU 固件、BIOS、ELF |
| 03–05 | GCC 编译汇编，教程手写 ROM/总线应答测试台，Verilator 执行 | 手写地址表不是 LiteX 自动分配的地址图 |
| 06 | SoCCore + SimPlatform + Builder，手动运行生成的仿真构建命令 | 输出 Verilog不等于已经执行 CPU |
| 07 | 加入裸机 C、链接脚本、数据/栈初始化，Builder 生成电路 | ELF 文件不是 FPGA 配置文件 |
| 08–11 | 先定 CSR 地址并生成头文件，再编 C，再生成同配置电路 | `csr.h` 是硬件定义的输出，不是手工猜的驱动地址 |
| 12 | 分别构造异步 SRAM/SDRAM/Flash 实验，按各入口区分模型与产物 | 不能把三类存储的结果都当同一套内存硬件 |
| 13 | 配置、先生成接口、编固件、构建集成仿真器，运行多个场景 | 场景日志/覆盖率不是 Builder 默认全部输出的 |
| 13A–13D | TAP/边界扫描、OpenOCD、GDB 的专门实验 | 工具日志不是 SoC 地址图或 FPGA bitstream |
| 14 | Tang Platform + Builder，生成电路、固件初值和板卡约束 | 没有在这一步完成综合和布局布线 |
| 15 | Yosys、nextpnr、Apicula 使用 14 的配套输入 | 不再通过 GCC 把 C 变成 FPGA LUT |
| 16–17 | 下载配置、读取真实串口、主机检查 | UART 日志不是布局布线报告 |
| 17A–17B | SMP 核心与共享内存 RTL 仿真，保存完整输入 | 双核仿真不能当作双核上板证据 |
| 18 | ICS55 标准单元映射、门级仿真、STA | FPGA 的 CST/.fs 不是 ASIC 工艺输出 |

## 3. LiteX 是怎样从 Python 走到文件的？

```text
实例化 SoCCore/子模块
  │ Signal、Memory、CSR、CPU Instance、总线连接成为电路对象
  ▼
soc.finalize()
  │ 整理模块、地址区域、CSR bank、IRQ、互连和核心源文件
  ├─ 形成 mem_regions / csr_regions / constants 等信息
  │         │
  │         ├─ Builder._generate_includes() → C 头文件/部分软件支持文件
  │         └─ Builder._generate_csr_map() → CSV/JSON/可选 SVD
  ▼
Platform/工具链生成构建工程
  │ Migen/LiteX 转换电路对象为 Verilog
  ├─ 导出 Memory 初值
  ├─ 把请求的板上资源变成引脚约束
  └─ 生成仿真或 FPGA 构建脚本
```

本地 LiteX 源码中的入口是 `litex/soc/integration/builder.py` 的 `_build()`、`_generate_includes()`、`_generate_csr_map()`；格式化输出在 `litex/soc/integration/export.py`，Verilog 输出在 `litex/gen/fhdl/verilog.py`。板卡约束/构建命令来自 `litex/build/` 下所选 Platform 和 toolchain。

这一流程有版本差异，应以本教程实际源码为准。单独调用私有 `_generate_*` 是本教程用于先生成软件接口的方式，不是所有 LiteX 工程都必须照搬。

## 4. 软件接口文件：它们为什么必须来自硬件？

常见位置：`builder/software/include/generated/`。

| 文件 | 生成者与输入 | 为什么生成 / 谁使用 |
| --- | --- | --- |
| `csr.h` | Builder 调用 `export.get_csr_header()`，输入 CSR 区域和对齐配置 | C 获得正确寄存器地址、位域和读写函数 |
| `soc.h` | Builder 将 SoC 常量导出为宏/访问辅助代码 | 软件知道时钟、CPU 特性、CSR 数据宽度等 |
| `mem.h` | Builder 导出内存区域起点、大小 | 软件可引用硬件的地址和容量 |
| `git.h` | Builder 导出相关版本标识 | 帮助确认构建用了哪份软件/硬件支持源码 |
| `variables.mak` | BIOS 软件构建路径下导出工具链、目录和 CPU 编译配置 | Make 使用这些构建变量 |
| `output_format.ld` | BIOS 路径按 CPU 生成链接输出格式 | 标准软件链接器获得正确目标格式 |
| `regions.ld` | BIOS 路径从内存区域生成链接片段 | 标准 LiteX 软件链接布局使用这些区域 |
| `sdram_phy.h` | 仅在有 SDRAM 时，按 PHY/时序/几何配置生成 | SDRAM 初始化软件使用配置序列 |
| `i2c.h` 等条件头文件 | 对应模块存在并使用相关生成路径时输出 | 提供该功能所需软件配置 |

这些文件并非每章都有。`with_bios=False` 的预生成步骤不输出所有 BIOS 专用文件。后续完整 `Builder.build()` 也可能生成软件支持文件，即使没有启用 BIOS 编译。

**看到 `regions.ld` 不代表本章固件一定使用它。** 我们的裸机固件常使用本章自己的 `linker.ld`；真正用哪个，以 GCC 命令中的 `-Wl,-T,...` 为准。

### 以 GPIO 读取为例

```text
Python：模块叫 gpio_in，CSRStatus 叫 input
      ↓ finalize 分配地址，生成 CSR bank
同一硬件定义 ─┬─→ RTL：收到该地址的读请求，返回 input.status
              └─→ csr.h：gpio_in_input_read() 内嵌该地址
```

C 函数通过普通 CPU load 读取外设。硬件接线决定状态值来自哪根输入；地址译码决定该 load 读哪个寄存器。名字方便人理解，硬件执行时主要使用地址。

### 4.1 三个头文件都有参数，但参数不只在导出函数里

```text
SoCCore 参数 + 外设 CSR 定义 + 内存区域 + 自定义常量
                         ↓ finalize
           ┌─────────────┼────────────────┐
           ▼             ▼                ▼
      csr_regions    constants        mem_regions
           │             │                │
           └─┬───────────┘                │
             ▼           ▼                ▼
       get_csr_header  get_soc_header  get_mem_header
             │           │                │
           csr.h        soc.h            mem.h
```

第一层参数决定真实硬件，第二层是导出格式。Builder 把已经确定的硬件信息传给导出函数，因此通常不需要你手工逐个填写寄存器地址。

下面按本地 LiteX 源码和第 14 章默认 Tang 结果说明。示例数字是当前选择，不是所有 LiteX 工程的固定值。

### 4.2 `csr.h`：哪些硬件参数决定内容？

| 参数/定义 | 在哪里设置 | 影响什么 |
| --- | --- | --- |
| 模块名称 | 例如 `self.add_module('leds', ...)` | 生成函数/宏的外设名前缀 |
| 寄存器名称 | 例如 `CSRStorage(1, name='output')` | 生成 `leds_output_write()` 等名称 |
| CSR 位宽 | `CSRStorage/CSRStatus` 的 size | 一个寄存器需要几个访问位置、C 如何拼接数值 |
| 只读/可写属性 | CSRStatus、CSRStorage 等定义 | 是否导出写函数以及硬件的访问行为 |
| CSR 字段定义 | CSRField 的名称、位置、宽度等 | 导出字段偏移/大小宏，供软件处理位域 |
| `csr_map` | SoC 类中的 bank 位置表 | 各外设 bank 使用哪个位置 |
| CSR 起始地址 | CPU/SoC 的内存映射中 `csr` 区域 | 最终 `CSR_BASE` 和寄存器字节地址 |
| `csr_paging` | SoCCore 参数，本地默认 `0x800` 字节 | 两个 bank 位置间的地址间距 |
| `csr_data_width` | SoCCore 参数，本地默认 32 位 | 一次 CSR 访问承载几位有效数据 |
| `csr_address_width` | SoCCore 参数，本地默认 14 位 | 内部 CSR 寻址容量，可容纳的 bank 范围 |
| CSR alignment | 本地 SoC 创建 CSR handler 时固定 32 位 | CSR 访问位置按 4 字节排列 |
| `csr_ordering` | SoCCore 参数，本地默认 `'big'` | 一个宽 CSR 拆成多个访问位置时，高/低部分的排列 |

本地源码没有把 `csr_alignment` 暴露为本章可随意传入的 SoCCore 参数；不能因为头文件里有 `CONFIG_CSR_ALIGNMENT`，就假定所有同名配置都能通过构造函数修改。

SoCCore 的相关参数可以这样显式写出：

```python
# 放在 SoCCore 构造参数中，示意当前默认配置
csr_data_width=32,
csr_address_width=14,
csr_paging=0x800,
csr_ordering='big',
```

它们是在描述电路和地址组织，修改后要重新生成硬件和固件，不能只手改头文件。

#### 第 14 章地址是怎样算出来的？

```python
csr_map = {'uart': 0, 'leds': 1, 'buttons': 2, 'identifier_mem': 3}
```

当前起点 `0xf0000000`，每个 bank 间距 `0x800`：

```text
UART bank    = 0xf0000000 + 0 × 0x800 = 0xf0000000
LED bank     = 0xf0000000 + 1 × 0x800 = 0xf0000800
按钮 bank    = 0xf0000000 + 2 × 0x800 = 0xf0001000
```

LED 的 output 是 bank 中第一个寄存器，偏移为零；UART 的 `txfull` 在当前寄存器排列中位于下一个 4 字节访问位置，所以地址是 `0xf0000004`。同一 bank 里若前面插入寄存器，后面偏移可能变化。

`csr_address_width=14` 指内部 CSR 地址宽度，不是 CPU 只有 14 位地址。在当前每位置 4 字节的对齐下，寻址窗口为 `2^14 × 4 = 65536` 字节；再除以 bank 间距，可以理解当前可用位置数量。实际还要满足 handler、CPU 和地址译码的限制。

#### `csr_ordering='big'` 为什么不和小端 CPU 冲突？

它决定**宽 CSR 的多次访问顺序**，不是 CPU 的字节端序。假设一个 64 位 CSR，数据宽度为 32：

```text
big：   base 读高 32 位，base+4 读低 32 位
little：base 读低 32 位，base+4 读高 32 位
```

生成的 C 函数按配置拼接两个值；每一次 32 位访问内部仍按 CPU 的内存端序处理。宽 CSR 是否能提供同一时刻的原子快照，还取决于外设设计，头文件不会自动保证。

### 4.3 `csr.h`：导出函数本身又有哪些选项？

当前 Builder 实际调用：

```python
export.get_csr_header(
    regions=self.soc.csr_regions,
    constants=self.soc.constants,
    csr_ordering=self.soc.csr.ordering,
    csr_base=self.soc.mem_regions['csr'].origin,
    cpu=self.soc.cpu,
    with_access_functions=True,
    with_fields_access_functions=False,
)
```

| 导出参数 | 用途 |
| --- | --- |
| `regions` | 已分配地址的 CSR 区域、寄存器和字段，不是手写地址字符串列表 |
| `constants` | 提供 alignment 等生成所需配置 |
| `csr_base` | 明确起点，生成 `CSR_BASE` 与地址关系 |
| `csr_ordering` | 默认多访问位置排列，区域可有自己的 ordering |
| `cpu` | 让地址导出/访问代码处理 CPU 特定映射等要求 |
| `with_csr_base_define` | 导出函数支持的选项，默认 True；控制基地址宏的表达方式 |
| `with_access_functions` | 是否生成寄存器读写函数；Builder 当前设为 True |
| `with_fields_access_functions` | 是否额外生成字段级访问函数；Builder 当前设为 False，字段宏仍可存在 |

这些是 `export.get_csr_header()` 的选项，不意味着 Builder 构造函数有同名参数。普通教程运行沿用 Builder 已写好的调用；若要调整格式，需要明确修改/扩展导出调用，而非猜一个构造参数。

生成头文件中的 `LITEX_CSR_ACCESS_FUNCTIONS` 也可在 C 预处理阶段控制访问函数是否参与编译。这不会改变硬件寄存器，也不会重新分配地址。

### 4.4 `soc.h`：哪些 SoC 参数会变成宏？

当前 Builder 调用 `export.get_soc_header(self.soc.constants)`。输入是硬件构造过程中汇总的常量集合。

| 原始配置/来源 | 第 14 章对应输出 | 含义 |
| --- | --- | --- |
| `clk_freq=27000000` | `CONFIG_CLOCK_FREQUENCY 27000000` | 软件编译时知道的系统频率 |
| Tang Platform | `CONFIG_PLATFORM_NAME "sipeed_tang_primer_20k"` | 平台身份 |
| `cpu_type='vexriscv'` | `CONFIG_CPU_TYPE_VEXRISCV` 等 | CPU 集成的类型/家族信息 |
| `cpu_variant='standard'` | `CONFIG_CPU_VARIANT_STANDARD`、缓存特性标志 | 所选核心配置的信息 |
| `cpu_reset_address=0` | `CONFIG_CPU_RESET_ADDR 0` | 配置的 CPU 复位入口 |
| CSR handler 的参数 | `CONFIG_CSR_DATA_WIDTH`、`CONFIG_CSR_ALIGNMENT`、ordering 标志 | 软件访问 CSR 所需配置 |
| 总线配置 | `CONFIG_BUS_STANDARD`、`CONFIG_BUS_DATA_WIDTH` 等 | 总线类型、宽度等信息 |
| IRQ 分配 | 例如 `UART_INTERRUPT 0` | 该外设的中断编号 |
| `ident` | `CONFIG_IDENTIFIER` | 标识字符串 |

不是构造函数的每个参数都逐字抄进 `soc.h`。CPU/外设集成会按各自规则登记常量；最终以 `self.soc.constants` 为准。IRQ 宏存在，也不表示固件已经启用或处理了这个中断。

可以在 SoC 中登记自定义软件常量：

```python
self.add_config('LESSON_TAG', 14)       # 输出 CONFIG_LESSON_TAG
self.add_constant('MAILBOX_MAGIC', 0x600d)  # 输出 MAILBOX_MAGIC
```

`add_config()` 帮你添加 `CONFIG_` 前缀，`add_constant()` 用指定名称登记。它们只提供常量信息，不会自动创建一个物理寄存器。

`get_soc_header(constants, with_access_functions=True)` 默认还为适合的常量生成 read 辅助函数，例如 `config_clock_frequency_read()`。该函数返回编译期数值，不是去 PLL 实时测量当前频率。无值的特性标志通常是 `#define CONFIG_CPU_HAS_ICACHE`，不应假定所有宏后都有数值。

### 4.5 `mem.h`：内存大小、地址和属性怎样传进来？

当前 Builder 调用：

```python
export.get_mem_header(self.soc.mem_regions, cpu=self.soc.cpu)
```

| 来源 | 怎样影响区域 |
| --- | --- |
| `integrated_rom_size`、ROM 映射 | 决定最终 ROM 起点、容量 |
| `integrated_sram_size`、SRAM 映射 | 决定片内 SRAM 区域 |
| `integrated_main_ram_size`、主 RAM 映射 | 决定本章数据/栈存储区域 |
| CPU/SoC `mem_map` | 提供默认区域起点；不同 CPU 集成可能不同 |
| 自定义 `SoCRegion(origin, size, mode, cached, ...)` | 新区域的地址、大小、访问和缓存等属性 |
| CPU 对地址的映射规则 | 导出 CPU 软件侧虚拟/别名地址时使用 |

导出读取的是 finalize 后的**实际区域**。容量可能受区域对齐/译码规则约束，不能仅看最初传入的字面值就认定最终输出一定一样。

第 14 章默认结果包含这样的宏：

```c
#define ROM_BASE      0x00000000L
#define ROM_SIZE      0x00002000
#define MAIN_RAM_BASE 0x40000000L
#define MAIN_RAM_SIZE 0x00004000
```

这里 SIZE 单位为字节，分别是 8192 和 16384。本地导出还生成 `*_BASE_VA` 以及区域说明字符串，供相关 CPU 软件映射/展示使用；默认 VexRiscv 配置中不能把 BASE_VA 的存在直接解释为启用了操作系统虚拟内存。

声明一个 `SoCRegion` 只是在描述地址区域；还需要相应的总线从设备/存储实现，地址才有实际应答。`mem.h` 宏也不会替你分配 RAM 或设置栈。

本章 `linker.ld` 由教程用配置另行生成，GCC 直接使用它。`mem.h` 是同一硬件信息的软件接口之一，不是本章链接脚本的唯一生产者。

### 4.6 改哪个参数，会连带更新哪些文件？

| 修改 | 应重做的关联步骤 |
| --- | --- |
| 外设名字、CSR 位宽/字段、bank 位置 | 重新 finalize，生成 csr.h/地址图/RTL，重编使用接口的 C |
| CSR paging/data width/ordering | 同时更新互连、头文件、地址检查和软件，不能只改 C 宏 |
| 系统时钟 | 更新 PLL/外设计时逻辑和 soc.h，重编依赖频率的固件并重做时序构建 |
| RAM 起点/大小 | 更新硬件区域、mem.h、地址图、链接布局和固件 |
| 自定义常量 | 重新生成 soc.h，并重编引用它的软件；是否还需改电路由常量用途决定 |
| 仅关闭导出的访问函数 | 改变 C 接口输出，不会删除硬件外设 |

最简单的可靠做法是从本章入口用同一配置重新生成配套文件。`csr.h`、`soc.h`、`mem.h` 是结果，不是编辑它们就能改变 FPGA 的配置入口。

## 5. 地址图文件：名字相似，来源不一定相同

| 文件 | 生产方式 | 为什么存在 |
| --- | --- | --- |
| `builder/csr.csv` | Builder → `export.get_csr_csv()` | 便于脚本/读者检查 CSR、常量与内存区域 |
| `builder/csr.json` | Builder → JSON 导出 | 为工具提供结构化地址信息，某些工程也可导入已有区域描述 |
| `.svd` | 配置了导出路径时由 Builder 生成 | 为调试工具提供外设寄存器描述 |
| 03–05 的 `memory_map.csv` | 本章 `write_handwired_maps()` 根据手写区域约定写出 | 记录测试台和程序共同遵守的地址合同 |
| 06 等的 `memory_map.csv` | 本章运行器复制 Builder 的 `csr.csv` | 把实际自动分配结果放在结果根目录，便于查看 |
| `irq_map.csv` | 本章运行器按验证情境写出/整理 | 说明中断号、来源和软件使用方式 |
| `csr-header.txt` | 本章运行器复制 `generated/csr.h` | 便于在结果根目录查看，不是另一套驱动 |

`memory_map.csv` 不一定只有“RAM 起点和大小”：若它是 CSR CSV 的副本，也包含 CSR 寄存器和常量行。读取时先看首列记录类型。

手写表描述预期；生成表描述实际硬件。核对两者的程序才是在检查地址合同，不能仅因为存在 CSV 就认定地址正确。

## 6. 固件产物：哪些是编译结果，哪些是教程转换？

```text
program.S 或 startup.S + main.c
          │ GCC，读取头文件/链接脚本/编译参数
          ▼
program.elf ── 链接器同时输出 ──→ program.map
     │                              │ 人读布局
     ├─ readelf ─→ sections.txt      │
     ├─ objdump ─→ disassembly.txt   │
     └─ objcopy -O binary           │
          ▼                         │
     program.bin                    │
          │ 教程 Python 按小端转换  │
          ▼                         │
     program.hex / rom_init.hex / ROM 字数组
          │
          ▼
     SoC Memory 初值或手写测试台 $readmemh
```

| 文件 | 内容与作用 |
| --- | --- |
| `linker.ld` | 链接规则，可能是本章源文件，也可能由本章配置生成；决定 ROM/RAM、区段和栈符号 |
| `test_config.h` / 其他配置头 | 本章生成的软件参数，不是 Builder 的标准固定文件名 |
| `program.elf` | 指令、区段、符号和入口元数据；便于调试/分析 |
| `program.map` | 链接器报告各区段/符号位置；不是硬件总线地址分配器 |
| `sections.txt` | 对 ELF 执行 readelf 保存的区段报告 |
| `disassembly.txt` | 对 ELF 执行 objdump 保存的实际指令 |
| `program.bin` | 提取的加载字节，不含完整 ELF 元数据 |
| `program.hex` | 本章将原始字节按约定转成文本；不是 GCC 的默认输出格式 |
| `rom_init.hex` | 通常进一步填满 ROM，可能加入本章校验/边界测试数据 |
| `program.sha256` 等 | 本章对某个文件求哈希，帮助核对版本与转换 |
| `compile-command.json` | 本章保存编译命令，帮助重现参数和头文件来源 |
| `link.log` | 本章保存 GCC/链接器标准输出与错误，失败先查它 |

不同章节的 `.hex` 格式和填充规则不同。03–05 每行是一个 32 位小端字；13 还加入自检校验信息；14 在 Python 内存中补齐后直接交给 Memory，使用生成的 `.init`。不要只按扩展名判断每行是字还是字节。

## 7. 顶层 RTL、核心 RTL、存储初值为何分开？

| 文件 | 来自哪里 | 用途 |
| --- | --- | --- |
| `sim.v` / `tutorial14.v` | LiteX/Migen 转换电路对象 | 描述该 SoC 的顶层、互连、外设和存储 |
| `VexRiscv.v` / SMP 集群 `.v` | CPU 数据包中的匹配预生成核心，必要时另调用核心生成器 | 实现顶层引用的 CPU 实例 |
| `Ram_*.v` 等核心附属模块 | CPU 数据包或相应库 | 实现核心引用的缓存/寄存器存储模块 |
| `*_rom.init` | Verilog Memory 初值导出 | 让 ROM 包含我们的程序字数组 |
| `*_sram.init` / `*_main_ram.init` | 对应 Memory 初值导出 | 支持仿真/综合的存储初始化输入 |
| `*_mem.init` | 按具体 Memory 实例导出，例如 Identifier | 名称不能单独说明用途，要追顶层 `$readmemh` 的数组 |
| `tb.sv` / 章节专用测试台 | 教程手写，收集器复制 | 提供激励、协议检查、超时、结束条件 |
| `*_primitives.v` | 库/教程保存的器件原语接口或模型 | 展开或数字仿真需要；不一定是实际硬宏行为 |
| `sources.json` | 教程收集器 | 记录文件来源、角色、哈希，防止遗漏核心依赖 |
| `files.f` | 教程或工具链保存的文件列表 | 指定某次展开/仿真使用哪些 HDL，不是逻辑电路本体 |

`rtl/` 是教程完整输入快照；`builder/gateware/` 是 Builder/工具链工程目录。前者可能额外收集安装目录中的核心依赖。复制时可能统一空白/换行，因此原文件与快照的哈希需分别记录。

空初值文件不会替代 C 的 `.bss` 初始化约定。启动代码仍须按软件规则清零，未初始化存储不能当作已经有确定软件值。

本地 Builder 还提供可选的 build bundle 输入归档路径，收集已解析的源码和软件依赖；只有启用了相关选项才有这类产物。它与教程的 `rtl/` 收集清单是两个机制，不能仅凭目录名混为一谈。

## 8. 仿真器文件：这里有两次“编译”

```text
RISC-V GCC：C/汇编 → RISC-V 指令 → 放在 ROM
                                            │
Verilator：RTL + 测试台 → 宿主 C++ → C++ 编译器 → Vsim/Vtb
                                            │
电脑执行 Vsim/Vtb → 模拟 CPU 电路 → 模拟 CPU 执行 ROM 中的指令
```

| 文件/目录 | 生成方式与用途 |
| --- | --- |
| `build_sim.sh` | SimPlatform 工具链生成，描述如何编译/运行仿真工程 |
| `sim.cpp` 等宿主支持源码 | 仿真工具链生成，连接时钟与所选模拟模块 |
| `obj_dir/Vsim*.cpp/.h`、`obj/Vtb*.cpp/.h` | Verilator 将 HDL 转成 C++ 模型 |
| `.o`、`.a`、Makefile | C++ 构建过程的对象、库和构建规则 |
| `Vsim` / `Vtb` | 电脑可执行仿真器，不是给 RISC-V CPU 执行的程序 |
| `modules/` 中的插件/库 | LiteX 仿真运行时所选时钟等模块；章节可能只编译需要的子集 |
| `.vcd` / `.fst` | 仿真执行期间在启用 trace 时写出的时序波形 |
| `run.log` / `normal.log` | 运行器保存仿真器输出 |
| `cases/*.uart.txt` | 测试台/运行器从 UART 位流提取字符后的文本 |
| 覆盖率文件 | 启用覆盖选项并执行用例后收集，不是仅生成 RTL 就得到 |

`Builder.build(run=False)` 的具体行为还受 `compile_gateware` 和所选工具链影响。本教程 06 的运行器会随后读取生成脚本、调用 Make、再启动 `Vsim`；14 则只交付 FPGA 构建输入。不能把这个参数当“所有工具永远不会编译”的统一保证。

## 9. FPGA 约束和布局布线文件

```text
Python Platform：器件、请求资源、球位、电平、时钟定义
             ↓ 工具链导出
CST/可用 SDC + RTL/初值
             ↓ Yosys
netlist.json、综合网表、综合报告
             ↓ nextpnr：器件数据库 + 接线约束 + 时序目标
routed.json、pnr-report.json
             ↓ Apicula 打包
tutorial14.fs
             ↓ openFPGALoader
FPGA 配置 SRAM → 电路开始工作
```

| 文件 | 谁产生、为什么存在 |
| --- | --- |
| `.cst` | Gowin Platform 工具链按资源表输出球位/电平，nextpnr 读取 |
| `.sdc` | 支持路径输出/本章显式写出的时序约束，是否存在取决于工具链 |
| `build_*.sh` | 工具链生成工具调用命令；文件存在不表示命令已成功执行 |
| `netlist.json` | Yosys 输出映射后的单元/连接，nextpnr 用作输入 |
| `routed.json` | nextpnr 写出实际放置坐标、连接和已使用布线资源，打包器读取 |
| `pnr-report.json` | nextpnr 的时序和资源报告；检查实际目标与裕量 |
| `.fs` / `.bit` | 相应器件配置格式；不是 ELF，也不是在 UART 上传的应用程序 |
| 布局图片 | 从 routed JSON/工具 GUI 提取的可视化；不是再一次综合，也不单独证明时序通过 |

不同目录可能有同名 `netlist.json`：下一步把前一步输出复制到自己的工作目录是正常的。判断是否同一份，核对源哈希/命令记录。

### ASIC 小实验的文件不要套用 FPGA 名称

第 18 章的 `mapped.v` 是 Yosys 按选定 Liberty 映射后的标准单元网表；PDK 的单元 Verilog 是库提供的仿真模型，收集到 RTL 目录并不表示我们生成了这套库。`constraints.sdc`、`timing.tcl` 是本章给 STA 的约束/命令；`timing.log` 是 OpenSTA 输出的保存结果。`pdk-lock.json` 记录下载版本/校验身份。它们服务于工艺映射与时序分析，不会产生可直接下载到 FPGA 的 `.fs`。

## 10. 报告、配置、清单是谁写的？

这些通常是**教程运行器**写的，不是 LiteX 固定的全部标准输出：

- `config.json`：本次实验输入参数。
- `manifest.json`：工具/配置/固件/RTL 的身份与来源记录。
- `summary.json`：运行器根据检查条件汇总的结论。
- `REPORT.md`：把检查结果写成人能读的说明。
- `commands.json`：记录外部工具命令。
- `negative.log`、`stale-map.log` 等：记录预期错误如何被捕获。
- `uart.log`：主机捕获的真实串口，时间戳通常来自主机。
- `load.log`、`detect.log`：下载器执行输出，由主机保存。
- `freeze.json`：本教程验收阶段保存的 RTL/配置/bitstream 哈希集合。

例如 06 的 `stale-map.log` 是地址图核对捕获旧地址时由 Python 写的，不是 CPU 自动打印的故障。相反，`run.log` 中的完成事务由实际仿真输出再被保存。两者都是证据，但证明的环节不同。

## 11. 如何自己追查一个陌生文件？

从仓库根目录开始：

```bash
# 查本章谁写它、复制它、调用外部工具产生它
rg -n 'csr-header|memory_map|program.map|write_text|copyfile|subprocess' \
  chapters/08-gpio

# 查原生 Builder 的导出逻辑（路径随 LiteX 源码安装位置调整）
rg -n '_generate_includes|_generate_csr_map|get_csr_header|platform' \
  ../litex/soc/integration/builder.py
```

直接 `write_text()` 常表示教程写出的内容；`copyfile()` 表示副本；`subprocess.run()` 的命令告诉你外部生产者。若文件由工具进一步产生，就继续读命令、构建脚本和日志。

最后核对“源码配置、头文件、固件、RTL、约束、报告”是否属于同一次生成。只修改结果中的头文件或地址表，不会自动改变已经综合或已经下载的电路。

## 12. 推荐怎么读一个结果目录？

```text
manifest/config：这是哪套配置？
      ↓
地址图 + 头文件：软件使用的地址与硬件一致吗？
      ↓
ELF/map/disassembly：程序在哪里，实际执行哪些指令？
      ↓
RTL + 初值 + 来源清单：完整电路输入是否齐全？
      ↓
工具/运行日志：实际执行到哪一步？
      ↓
summary/report：结论由什么检查支持，哪些仍没做？
```

遇到 `status=PASS`，需要知道它是生成通过、展开通过、CPU 仿真通过、布局布线通过还是实物运行通过。上一步的输出是下一步的输入，但上一步成功不能自动替下一步背书。
