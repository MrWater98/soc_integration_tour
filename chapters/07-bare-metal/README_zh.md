# 第 07 章：给 SoC 加主 RAM，运行一段裸机 C

本章不依靠 BIOS 或操作系统，直接让 VexRiscv 从 ROM 中的启动代码进入 C 的 `main()`。工作 RAM 开始存放 `.data`、`.bss`、栈和测试数据。

## 输入

- 本章自己的 [`soc.py`](soc.py) 定义带 main RAM 的 LiteX SoC；运行时由 Builder 生成并核对本章地址图。
- RISC-V GCC、objcopy、objdump、readelf；本章新增 `main.c`、`startup.S`、`linker.ld`。
- 本章自己的 `baremetal.py` 和 `litex_builder.py` 分别处理 ELF/ROM 镜像与 SoC 构建、仿真。
- 16 KiB main RAM、4 KiB 启动 ROM、4 KiB LiteX SRAM；完成端点继续作为仿真检查口。

## 概念速查

| 名词 | 一句话记住 | 本章在哪里看 |
| --- | --- | --- |
| 裸机 | 程序直接运行在硬件上，没有操作系统替你初始化内存 | `startup.S` 直接 `call main` |
| ELF | 带入口、段地址和符号的链接结果 | `program.elf`、`readelf` 输出 |
| linker script | 告诉链接器每种程序内容应该放进哪块内存 | `linker.ld` 的 `MEMORY` 与 `SECTIONS` |
| `.text` | CPU 要执行的指令 | ELF 中 VMA 从 ROM 地址 0 开始 |
| `.rodata` | C 的只读常量数据，通常随代码放进 ROM | `linker.ld` 把它接在 `.text` 后；本章小程序没有专门的常量表 |
| `.data` | 有初始值的可写全局变量 | ELF 的运行地址在 main RAM，加载副本在 ROM |
| `.bss` | 初值为 0 的全局/静态变量 | ELF 中是 `NOBITS`，启动代码清零 |
| LMA / VMA | 镜像存放地址 / 程序运行地址 | `objdump -h` 的 LMA、VMA 两列 |
| 栈 | 函数调用保存返回地址与局部变量的 RAM 区域 | `sp` 从 `__stack_top` 向下增长 |
| `volatile` | 告诉编译器每次都要真的读写这个内存或寄存器 | `main.c` 的 RAM 与完成寄存器指针 |
| 堆 | 运行时按需分配的内存区域；本章只标出可用范围，不调用 `malloc` | `__heap_start` 到 `__heap_end`，位于 BSS 后、栈保留区前 |

## 启动路径图

```text
复位 PC=0
   │
   ▼
ROM: _start ──设置 sp──────────────> main RAM 顶端
   │          ──复制 .data 的 LMA→VMA──> main RAM
   │          ──把 .bss 清零────────> main RAM（仿真初值故意设为 A5）
   ▼
main(): 检查初值/零值、读写 scratch、嵌套调用用栈函数
   │
   └──写 0x5a 到完成端点────────────> 仿真 PASS
```

输入是 ELF 链接规则、C/汇编源文件和 SoC 地址图；输出是 ELF、ROM 加载镜像、链接地图、段表、反汇编和 CPU 完成记录。

## `.data` 是怎样从 ROM 搬到 RAM 的？

这不是 ROM 主动把数据推到 RAM，也不是 LiteX 在仿真开始时替 CPU 复制。链接器安排好两处地址，CPU 执行 `_start` 中的 `lw` 和 `sw`，一字一字搬过去。

链接脚本里的 `.data ... > main_ram AT > rom` 同时指定两件事：`.data` 在程序运行时位于 main RAM（VMA），它的初始字节则存放在 ROM 镜像中（LMA）。`__data_load_start` 是 ROM 源地址，`__data_start` 和 `__data_end` 是 RAM 目的范围。

```text
链接时：initialized_data 的初始值放进 ROM 镜像

运行时：CPU 执行 _start
ROM 0x0000019c ── lw ──> CPU 寄存器 t3 ── sw ──> RAM 0x40000000
                       0x11223344
```

本次生成的地图里，`__data_load_start = 0x0000019c`，`__data_start = 0x40000000`，`__data_end = 0x40000004`。所以本例 `.data` 长 4 字节，只循环一次。对应启动汇编是：

```asm
lw   t3, 0(t0)    # t0 指向 ROM 加载地址，读一个 32 位字
sw   t3, 0(t1)    # t1 指向 RAM 运行地址，把这个字写入 RAM
addi t0, t0, 4    # 源地址前进 4 字节
addi t1, t1, 4    # 目的地址前进 4 字节
```

`la` 把链接器给出的符号地址放进寄存器；循环在目的指针到达 `__data_end` 时停止。`lw` 读 ROM，`sw` 写 RAM，二者都是 CPU 的普通 load/store 事务，由 SoC 地址译码把访问送到对应存储器。`t3` 是中途暂存数据的 CPU 寄存器。

## 为什么还要清 `.bss`？

`.bss` 放的是有静态存储期、按 C 规则应当初值为零的变量。本章的 `zero_initialized` 没有显式赋值，`scratch[4]` 也没有显式赋值，因此它们都应在 `main()` 开始前为零。链接脚本把 `.bss` 标为 `NOLOAD`：它不带一份 ROM 初始数据，不能指望从 ROM 拷贝出零来。

因此 `_start` 用 `__bss_start` 和 `__bss_end` 遍历这块 RAM，并逐字写入 0。实际构建中 `.bss` 范围是 `[0x40000004, 0x40000018)`，包含 `zero_initialized` 和 4 个 `scratch` 元素。

仿真把 main RAM 预先填成 `0xa5a5a5a5`，这是为了让“忘了清 `.bss`”变成可见错误，而不是碰巧读到 0。若去掉清零循环，`zero_initialized` 和 `scratch[0]` 会读到哨兵值 `0xa5a5a5a5`，C 检查就不会通过；只有检查通过，程序才向完成端点写成功码 `0x5a`。真实 RAM 上电后的内容通常没有这种保证，不能把它当作零。

```text
RAM 仿真初值： A5 A5 A5 A5 A5 A5 ...
                   │ _start 对 .bss 逐字写 0
                   ▼
main() 看到：   00 00 00 00 00 00 ...
                └─ zero_initialized 和 scratch[0] 都通过检查
```

## 最小实现与参数

[`linker.ld`](linker.ld) 把 `.text` 放在 ROM，把 `.data` 的运行地址放在 `main_ram`、加载地址放在 ROM；`.bss` 和栈都位于 main RAM。启动汇编逐字拷贝 `.data`，再逐字写零清理 `.bss`。仿真先把整块 main RAM 填成 `0xa5a5a5a5`：若启动代码忘了清零，`zero_initialized` 和 `scratch[0]` 不会碰巧为零。C 程序检查变量初值，读写独立的 `scratch` 缓冲区，调用 `stack_roundtrip()` → `use_stack()`；运行器还检查反汇编确实有两个函数，以及 `stack_roundtrip` 保存、恢复返回地址 `ra`。

| 参数 | 本章值 | 选择理由 |
| --- | ---: | --- |
| ROM | 4 KiB，字节地址 0 | CPU 复位后要从这里取 `_start` |
| main RAM | 16 KiB，字节地址 `0x40000000` | 放数据段、BSS、栈和工作数据 |
| 栈余量断言 | 至少 256 B | 链接器在 RAM 太小时给出明确失败 |
| 编译 ISA / ABI | `rv32i2p0` / `ilp32` | 与 VexRiscv minimal 的指令配置一致 |
| 优化等级 | `-O1`，函数标记 `noinline` | 保留真实嵌套调用，同时避免不必要的库依赖 |
| 完成码 | `0x5a` 成功，`0xe1` 失败 | 错误时显示 `SOC_FAIL` 并结束仿真，不能伪造 PASS |

本章另运行一个 256-byte main RAM 的**预期链接失败**案例。它证明链接器发现段和栈余量不够；这是构建期检查，不是 CPU 运行时失败。

链接脚本用 `__heap_start` 和 `__heap_end` 标出堆的候选空间：它从 `.bss` 后开始，在栈底保留量前结束。当前程序没有堆分配器，因而不会实际使用该空间；真实运行时还需要检查堆增长不与栈碰撞。

## 本章在 SoC 配置上增加了什么？

本章沿用前面已经建立的 CPU、复位向量、ROM 和 LiteX SRAM 配置，重点新增可写 main RAM，给 C 运行时放 `.data`、`.bss` 和栈。参数仍集中在 `ProjectSoC` 的 `super().__init__(...)` 调用中：

| 参数 | 第 07 章的值 | 对本章有什么用 |
| --- | --- | --- |
| `integrated_main_ram_size` | `16 * 1024` 字节 | 把 16 KiB main RAM 接入 SoC，地址为 `0x40000000`；linker script 把 `.data`、`.bss` 和栈放到这里。 |
| `integrated_main_ram_init` | `[0xa5a5a5a5] * 4096` | 仿真开始时给 16 KiB RAM 每个字填哨兵值，让漏掉 `.bss` 清零时一定能被固件发现。 |
| `integrated_sram_size` | `0x1000`（4 KiB） | 保留另一块独立 SRAM，当前 map 中位于 `0x10000000`。本章 linker script 不把 C 数据和栈放在那里；保留它是为了区分 LiteX SRAM 与 main RAM。 |

复位地址仍是 `0`，ROM 也仍从 `0` 开始。本章 linker script 用 `ENTRY(_start)` 声明 ELF 入口，并通过 `KEEP(*(.text.init))` 把 `_start` 放在 ROM 最前面。注意 `ENTRY` 只是 ELF 元数据；真正让 CPU 从 0 开始取指的是 VexRiscv 的复位向量配置。两者和 ROM 内容对齐后，CPU 才能从复位直接执行 `_start`。

本章自己的 `CompletionSlave` 负责测试收尾：CPU 写入 `0x5a`，它打印 `SOC_COMPLETE` 并结束仿真。它不属于 C 运行时，也不负责 `.data` 复制或 `.bss` 清零。

## 常见问题

### 为什么复位后不能直接进入 `main()`？

复位只让 CPU 从复位地址取指，不会替 C 运行环境准备数据。`_start` 先把有初值的 `.data` 从 ROM 的加载地址拷贝到 RAM 的运行地址，再清零 `.bss`、设置 `sp`，最后才调用 `main()`。少了其中一步，C 全局变量的初值或零值就不可靠。

### LMA 和 VMA 分别指什么？

LMA 是初始镜像存放的位置；VMA 是程序运行时访问该段的位置。`initialized_data` 的初始字节放在 ROM 的 `.text` 后面，但 C 代码使用它时地址位于 main RAM。启动代码负责把这两处连起来。可以在 `sections.txt` 或 `objdump -h` 中对照查看。

### 为什么没清 `.bss` 时检查会失败？

全局变量 `zero_initialized` 和 `scratch` 按 C 规则应当初值为零，但它们在 ELF 的 `.bss` 里，不占 ROM 初始化字节。LiteX 仿真先把 main RAM 填成 `0xa5a5a5a5`，启动代码必须逐字覆盖 `.bss`。`main()` 在改写 `scratch[0]` 之前先检查 `zero_initialized==0` 和 `scratch[0]==0`；漏清零时会读到 `0xa5a5a5a5`，写入的是失败码而不是 `0x5a`。这项预填是仿真用的哨兵，真实 RAM 的上电值不一定是 A5，但同样不能假设它天然为零。

### 256 字节负例说明什么？

链接脚本的 `ASSERT` 要求程序段和最小栈余量能放进 RAM。运行器用 256 字节重新链接，并期待链接器拒绝。它证明容量问题在构建阶段被发现，不代表 CPU 曾在 256 字节 RAM 上运行。

### 为什么再检查 `ra` 和 `sp`？

`main()` 调 `stack_roundtrip()`，它再调 `use_stack()`。第二层 `jal` 会覆盖 `ra`，所以外层函数要在栈帧里保存并恢复返回地址。运行器从反汇编寻找 `sw ra,...(sp)` 和 `lw ra,...(sp)`；CPU 最后的完成码再证明这些嵌套调用确实返回，C 检查也执行到了。

## 运行与输出
本章完整的仿真 RTL 输入集保存在 [`results/07/rtl`](../../results/07/rtl)：生成的 SoC 顶层、对应的 Vex CPU 与 RAM 模块、所有引用的存储器初始化文件，以及 `rtl_sources.txt`。

```sh
python3 chapters/07-bare-metal/run.py
```

预期先见 `EXPECTED_FAIL 07-SMALL-RAM`，然后正常案例写出 `SOC_COMPLETE ... 0x5a` 和 `PASS 07`。输出在 `results/07/`：

| 文件 | 读法 |
| --- | --- |
| `firmware/program.elf` | 完整 ELF，可运行 `riscv64-unknown-elf-readelf -S` |
| `firmware/program.map` | 每个符号/段被链接到哪个地址 |
| `firmware/sections.txt` | `.text/.data/.bss` 的类型、VMA、大小 |
| `firmware/disassembly.txt` | 机器码对应的启动拷贝、清零、函数调用指令 |
| `builder/csr.csv`、`memory_map.csv` | LiteX SoC 的 ROM、SRAM、main RAM 与 IO 地址 |
| `irq_map.csv` | 只有表头；本章尚未加入中断源 |
| `builder/gateware/sim_main_ram.init` | 4096 个非零初值字；运行器逐字检查 |
| `small-ram/negative.log` | 256 B 配置被链接器拒绝的证据 |
| `run.log`、`builder/gateware/sim.vcd` | CPU 完成记录与总线波形 |

重点对照 `disassembly.txt` 与 `linker.ld`：`_start` 地址在 ROM，`initialized_data` 的运行地址在 `0x40000000`，但它在镜像中的加载副本紧随 `.text`。启动指令正是把这两处接起来。`.bss` 的 ELF 类型是 `NOBITS`，不占 ROM 初始化字节，因此必须由启动代码归零。打开反汇编搜索 `<stack_roundtrip>:`，其中的 `sw ra,28(sp)` 与 `lw ra,28(sp)` 是函数调用前后把返回地址放入栈、再取回的直接证据。`run.log` 的 `SOC_COMPLETE ... data=0x0000005a` 表示这些 C 检查通过；若只看到 ELF 或非零初值文件，仍不能断言 CPU 执行成功。

## 常见问题与下一步

- 256 B 负例出现 linker `ASSERT`：这是预期结果；查看 `small-ram/negative.log` 中栈余量报错。
- 正常仿真超时：检查 `.data` 有没有被放入复制范围，VMA/LMA 是否合理，主 RAM 是否在 `memory_map.csv` 中，以及 CPU 编译 ISA 是否匹配。
- 只有 ELF 不够：SoC 启动 ROM 需要加载镜像；链接器地图还要确认每个 VMA/LMA 符合硬件地址图。

进入第 08 章前，能从链接表找出 `.text/.data/.bss`，解释启动代码为什么拷贝和清零，并从波形或日志确认程序曾读写 main RAM 与完成端点。

## 本章速记

1. linker script 决定段落在哪个地址；`objdump -h` 用 LMA/VMA 展示“存在哪”和“运行在哪”。
2. CPU 复位只会取指，不会替 C 运行时复制 `.data` 或清零 `.bss`。
3. `sp` 在 RAM 顶端，函数栈帧向低地址扩展；链接时要给栈留余量。
4. ELF/地图证明构建结果；完成码证明 CPU 执行到了检查点。
