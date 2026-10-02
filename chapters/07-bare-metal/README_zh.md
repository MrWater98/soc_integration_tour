# 第 07 章：给 SoC 加主 RAM，运行一段裸机 C

本章不依靠 BIOS 或操作系统，直接让 VexiiRiscv 从 ROM 中的启动代码进入 C 的 `main()`。工作 RAM 开始存放 `.data`、`.bss`、栈和测试数据。

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
ROM: _start ──复制 .data 的 LMA→VMA──> main RAM
   │          ──把 .bss 清零────────> main RAM（仿真初值故意设为 A5）
   │          ──设置 sp─────────────> main RAM 顶端
   ▼
main(): 检查初值/零值、读写 scratch、嵌套调用用栈函数
   │
   └──写 0x5a 到完成端点────────────> 仿真 PASS
```

输入是 ELF 链接规则、C/汇编源文件和 SoC 地址图；输出是 ELF、ROM 加载镜像、链接地图、段表、反汇编和 CPU 完成记录。

## 最小实现与参数

[`linker.ld`](linker.ld) 把 `.text` 放在 ROM，把 `.data` 的运行地址放在 `main_ram`、加载地址放在 ROM；`.bss` 和栈都位于 main RAM。启动汇编逐字拷贝 `.data`，再逐字写零清理 `.bss`。仿真先把整块 main RAM 填成 `0xa5a5a5a5`：若启动代码忘了清零，`zero_initialized` 和 `scratch[0]` 不会碰巧为零。C 程序检查变量初值，读写独立的 `scratch` 缓冲区，调用 `stack_roundtrip()` → `use_stack()`；运行器还检查反汇编确实有两个函数，以及 `stack_roundtrip` 保存、恢复返回地址 `ra`。

| 参数 | 本章值 | 选择理由 |
| --- | ---: | --- |
| ROM | 4 KiB，字节地址 0 | CPU 复位后要从这里取 `_start` |
| main RAM | 16 KiB，字节地址 `0x40000000` | 放数据段、BSS、栈和工作数据 |
| 栈余量断言 | 至少 256 B | 链接器在 RAM 太小时给出明确失败 |
| 编译 ISA / ABI | `rv32im` / `ilp32` | 与单核 VexiiRiscv 32 位配置一致 |
| 优化等级 | `-O1`，函数标记 `noinline` | 保留真实嵌套调用，同时避免不必要的库依赖 |
| 完成码 | `0x5a` 成功，`0xe1` 失败 | 错误时显示 `SOC_FAIL` 并结束仿真，不能伪造 PASS |

本章另运行一个 256-byte main RAM 的**预期链接失败**案例。它证明链接器发现段和栈余量不够；这是构建期检查，不是 CPU 运行时失败。

链接脚本用 `__heap_start` 和 `__heap_end` 标出堆的候选空间：它从 `.bss` 后开始，在栈底保留量前结束。当前程序没有堆分配器，因而不会实际使用该空间；真实运行时还需要检查堆增长不与栈碰撞。

## 常见问题

### 为什么复位后不能直接进入 `main()`？

复位只让 CPU 从复位地址取指，不会替 C 运行环境准备数据。`_start` 先把有初值的 `.data` 从 ROM 的加载地址拷贝到 RAM 的运行地址，再清零 `.bss`、设置 `sp`，最后才调用 `main()`。少了其中一步，C 全局变量的初值或零值就不可靠。

### LMA 和 VMA 分别指什么？

LMA 是初始镜像存放的位置；VMA 是程序运行时访问该段的位置。`initialized_data` 的初始字节放在 ROM 的 `.text` 后面，但 C 代码使用它时地址位于 main RAM。启动代码负责把这两处连起来。可以在 `sections.txt` 或 `objdump -h` 中对照查看。

### 怎么确认 `.bss` 确实被清零了？

仿真会先把 main RAM 的 4096 个字填成 `0xa5a5a5a5`。如果启动代码没清 `.bss`，`zero_initialized` 和 scratch 缓冲区就不会碰巧是 0。固件检查这些变量后才写完成码。

### 256 字节负例说明什么？

链接脚本的 `ASSERT` 要求程序段和最小栈余量能放进 RAM。运行器用 256 字节重新链接，并期待链接器拒绝。它证明容量问题在构建阶段被发现，不代表 CPU 曾在 256 字节 RAM 上运行。

### 为什么再检查 `ra` 和 `sp`？

`main()` 调 `stack_roundtrip()`，它再调 `use_stack()`。第二层 `jal` 会覆盖 `ra`，所以外层函数要在栈帧里保存并恢复返回地址。运行器从反汇编寻找 `sw ra,...(sp)` 和 `lw ra,...(sp)`；CPU 最后的完成码再证明这些嵌套调用确实返回，C 检查也执行到了。

## 运行与输出

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
