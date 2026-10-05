# 06 —— 让 LiteX 来构造 SoC

01–05 章逐一弄清 CPU 复位、Wishbone 应答、ROM 镜像、可写 SRAM 和地址译码。本章用 LiteX `SoCCore` 与 `Builder` 描述同类系统，检查 LiteX 生成的地址图是否符合固件约定，再运行 CPU。

## LiteX 接管了哪些工作？

`SoCCore` 注册 CPU 并建立 SoC 基础设施：主总线、集成 ROM/SRAM、CSR 访问路径和 CPU 相关地址区域。`Builder` 根据这份 Python 描述生成 gateware、仿真文件、CSR/地址表和软件支持文件。项目仍保留一个小型完成端点，让仿真在固件写出完成标志时结束。

```text
soc.py：SoCCore 参数 + 项目完成端点
        │
        ▼
LiteX Builder：gateware、csr.csv/csr.json、仿真工程
        │
        ├── check_generated_map：地址图与固件约定比较
        └── 编译 Verilator 模型 → 运行 VexiiRiscv → 检查 SOC_COMPLETE
```

## 本章的 `SoCCore` 配置对应什么实验？

这里沿用 LiteX SoC 的 CPU、主总线和 CSR 结构，重点是让 `SoCCore` 集成 ROM 与 SRAM，再由 Builder 导出地址图。`ProjectSoC` 的配置和固件检查一一对应：

| 参数 | 第 06 章的值 | 为什么这样设置 |
| --- | --- | --- |
| `cpu_reset_address` | `0` | 仍从 ROM 地址 0 启动。LiteX 将 ROM 映射到复位地址，固件也从这里开始。 |
| `integrated_rom_size` | `0x1000`（4 KiB） | 比最小启动实验的 ROM 更大，便于检查 ROM 的首地址和末地址。 |
| `integrated_rom_init` | `write_rom_init(...)` 生成的 1024 个字 | `cpu_sim.py` 编译固件，补齐 ROM 镜像，并把末字设为 `0x5a6b7c8d`，供程序做边界读回。 |
| `integrated_sram_size` | `0x1000`（4 KiB） | 创建 LiteX SRAM。`program.S` 对首字、末字都做写入和读回，验证 Builder 生成的 SRAM 区域确实可访问。 |
| `integrated_main_ram_size` | `0` | 本章是汇编测试，不需要 C 数据区或栈；SRAM 测试由程序直接访问。 |
| `with_uart / with_timer / with_ctrl` | 都为 `False` | 本章不测试这些外设，关闭它们避免额外模块干扰地址图。 |
| `ident` | `"SoC Integration Tour Stage 06"` | 标识这次生成的 LiteX SoC。 |

CPU 类型、变体、`platform` 和时钟配置在 `soc.py` 的 `super().__init__(...)` 中也明确给出。未指定的总线参数采用 LiteX 默认值；此处 LiteX 主总线为 Wishbone，VexiiRiscv 外设口为 AXI-Lite，因此 LiteX 自动插入协议适配器。

4 KiB ROM/SRAM、1024 字镜像和关闭外设都是本章的配置，目的是清楚地观察首末边界读写，并减少无关模块。调整 ROM 时，要让 `write_rom_init`、`integrated_rom_size`、链接/镜像构建和 `check_generated_map` 保持一致；调整 SRAM 容量或区域地址时，也要更新固件访问地址和预期地址图。这些数值不是 LiteX 的固定要求。

本章 `CompletionSlave` 仍是项目自己的仿真端点。它和 SoCCore 自动集成的 ROM/SRAM 不同：端点只负责记录固件探针和完成码，并在成功后结束仿真。

## 常见问题

### `AXILite2Wishbone` 到底在哪里调用？

它是 LiteX 原生适配器，不会由某个章节 Python 文件直接调用。VexiiRiscv 暴露 AXI-Lite 外设总线，而这里 `SoCCore` 的主总线是 Wishbone。LiteX 注册 CPU master 时，`add_master()` / `add_adapter()` 会查询协议转换关系，并从 `litex/soc/interconnect/axi/axi_lite_to_wishbone.py` 实例化 `AXILite2Wishbone`。

```text
cpu_type="vexiiriscv"
    → 原生 VexiiRiscv 封装提供 AXI-Lite pBus
    → SoCCore 把 cpu_bus0 注册到 Wishbone 主总线
    → LiteX 插入 AXILite2Wishbone
    → ROM、SRAM、项目端点通过 Wishbone 应答
```

构建日志中的 `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit` 是这次构建插入桥的直接证据。桥负责协议和地址表示转换；它本身不会决定软件 memory map。项目增加 Wishbone 端点，不重复实现协议桥。

### `tour_paths.add_litex_to_path` 是什么？

它是仓库根目录 `tour_paths.py` 里的项目辅助函数，不是 LiteX API，也不是硬件模块。它根据 `LITEX_ROOT` 和项目约定位置寻找 LiteX 源码，然后加入 Python 导入路径。它不会安装 LiteX，也不会下载源码。各章逻辑文件保留在本章目录；这个共享脚本只负责寻找依赖。

### 其他导入的辅助函数分别做什么？

下列函数属于本章 `run.py` 旁边的项目脚本，并非 LiteX 内置 API：

| 函数 | 输入 | 做什么 | 输出 |
| --- | --- | --- | --- |
| `cpu_sim.py` 的 `build_program(chapter, build_name=...)` | 本章 `program.S` 和输出目录名 | 调 RISC-V GCC 生成 ELF，调用 `objcopy` 得到二进制，再按小端序每 4 字节打包 | `results/06/firmware/` 下的 `.elf`、`.bin`、`.hex` 和哈希 |
| `cpu_sim.py` 的 `write_rom_init(out, 1024, ...)` | 程序字数和 ROM 深度 | 检查容量、补足空余字、可选地写入末字测试值 | 1024 字的 `rom_init.hex` 和传给 `SoCCore` 的整数列表 |
| `soc.py` 的 `ProjectSoC(platform, rom_words=...)` | SimPlatform 和初始化 ROM 内容 | 配置 `SoCCore` 并挂接仿真完成端点 | LiteX SoC 描述 |
| `litex_builder.py` 的 `build_and_run(...)` | SoC 构造函数、预期地图、完成日志文字 | 调 LiteX Builder，检查生成文件，编译仿真器、运行并检查日志 | Builder 输出目录和构建/编译/运行证据 |
| `check_generated_map(csr.csv, regions=...)` | Builder CSV 和预期字节范围 | 比较每个生成 memory region 的起点和容量 | 匹配则继续，不匹配抛出 `AssertionError` |

`build_and_run` 是项目包装流程，不是 LiteX API；它内部调用 LiteX 的 `Builder`。`build_program` 是用 Python 调用外部 RISC-V 编译器，也不负责编译 CPU 硬件。

### 为什么地址图变了就要重新编译固件？

固件的指令里包含访问地址。第 05 章把 SRAM 放在 `0x00010000`、寄存器端点放在 `0x20000000`；LiteX 在本章生成的地址图把 SRAM 放在 `0x10000000`、完成端点放在 `0x80000000`。继续用旧固件会访问错误区域。因此本章用自己的 `program.S` 按 LiteX 新地址重新汇编，并在仿真前将预期起点、容量与 `csr.csv` 比较。

### `csr.csv` 能证明什么？不能证明什么？

`csr.csv` 和 `csr.json` 展示构造阶段生成的地址与容量，证明 LiteX 生成了哪张地址图；它们不能证明 CPU 已经取指或完成总线事务。`run.log` 中 CPU 写出 `SOC_COMPLETE` 才是运行证据。运行器还会故意拿第 05 章的旧地图做检查，要求它被拒绝，并把原因记入 `stale-map.log`。

### 完成日志里的 `0x200003ff` 是什么地址？

地图使用字节地址。完成端点的最后一个字节地址是 `0x80000fff`，固件向末尾 32 位字节地址 `0x80000ffc` 写入。按字寻址的 Wishbone 上它是 `0x80000ffc / 4 = 0x200003ff`。日志写明 `word_address`，表示这是字地址，不是软件字节地址。

## 运行与观察

```sh
PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py
```

脚本按下面顺序执行：

```text
寻找 LiteX 源码 → 按本章地址编译固件 → 生成完整 ROM 镜像
→ 实例化 ProjectSoC → 运行 Builder → 将 csr.csv 和预期区域比较
→ 编译仿真器 → 运行 CPU → 要求日志出现 SOC_COMPLETE
```

查看 `results/06/builder/csr.csv` 中 Builder 的地址图、`results/06/memory_map.csv` 中的副本、`build.log` 中 AXI-Lite 到 Wishbone 的适配记录，以及 `run.log` 中的 CPU 运行信息。`compile.log` 是仿真器构建日志；`builder/gateware/sim.vcd` 可观察时钟/复位、CPU AXI-Lite 信号、桥后的 Wishbone 和完成端点。

## PASS 能证明什么？

地址检查证明 LiteX 生成的 memory region 与固件约定相符。运行时完成标志证明 CPU 执行了镜像，并通过集成系统写到了预期端点。它们都不覆盖板级引脚约束、FPGA 时序收敛或外部存储器硬件；这些是后续阶段的工作。
