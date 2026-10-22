# 14.2：从寄存器地址到 C 驱动，再到 ROM 中的指令

先打开 [main_tang.c](../../main_tang.c)、[startup.S](../../startup.S)，以及同章 [firmware.py](../../firmware.py) 中的 `firmware()`。本篇中的地址来自默认 Tang 结果。

## 1. “驱动”在这个裸机程序里是什么？

```text
外设电路：UART、GPIO、CSR 寄存器
          ↑ CPU 普通 load/store
访问函数：generated/csr.h
          ↑ C 函数调用
小驱动：character/text/hexadecimal
          ↑
应用逻辑：打印启动消息、读按钮、写 LED
```

这里没有操作系统，CPU 直接访问外设地址。`csr.h` 的函数是自动生成的薄访问层；`character()` 等是我们编写的软件逻辑。

别混淆两种 CSR：LiteX CSR 是外设的内存映射寄存器；RISC-V `mstatus` 等 CSR 是 CPU 内部寄存器，用 `csrr/csrw` 一类指令访问。本章 GPIO/UART 用普通内存访问。

## 2. 地址是谁决定的？

```python
csr_map = {'uart': 0, 'leds': 1, 'buttons': 2, 'identifier_mem': 3}
```

这些数字是 CSR bank 的位置，不是最终字节地址。当前 CSR 起点为 `0xf0000000`，bank 间距为 `0x800` 字节：

| 外设寄存器 | 本次字节地址 | 用途 |
| --- | --- | --- |
| UART `rxtx` | `0xf0000000` | 写发送字节；读接收数据 |
| UART `txfull` | `0xf0000004` | 发送 FIFO 是否满 |
| UART `ev_enable` | `0xf0000014` | UART 事件中断使能 |
| LED `output` | `0xf0000800` | CPU LED 的一位逻辑值 |
| 按钮 `input` | `0xf0001000` | 同步后的按钮状态 |
| Identifier bank | `0xf0001800` | 标识存储区 |

bank 间距、CSR 宽度/对齐和 CSR 起点都是配置。一个一位 GPIO 占了一个访问位置，不代表它包含 32 个物理 GPIO；64 KiB CSR 区域也不意味着占用了 64 KiB 块 RAM。

LiteX 在 `soc.finalize()` 时组织 CSR bank 和地址。`Builder._generate_includes()` 调用 LiteX 的 `export.get_csr_header()`，把同一张硬件地址图输出为 `generated/csr.h`。

## 3. 一个函数怎么知道要读什么？

生成的代码：

```c
static inline uint32_t buttons_input_read(void) {
    return csr_read_simple((CSR_BASE + 0x1000L));
}
```

本章配置下，访问等价于从 `0xf0001000` 读取一个 volatile 32 位值：

```text
函数名 buttons_input_read
             ↓ 内置生成好的地址
CPU load 0xf0001000
             ↓ Wishbone 译码到 CSR 区
Wishbone2CSR → 选中 buttons bank → 选中 input
             ↓
返回 ButtonInput 中同步后的按键状态
```

这个函数没有运行时搜索引脚。Python 已经接好“按键 → 状态寄存器”，硬件地址译码已经接好“地址 → 那个寄存器”。软件只需要发出该地址的读请求。

## 4. `volatile` 为什么重要？

LiteX 的 `hw/common.h` 在当前 32 位 CSR 配置下定义：

```c
#define CSR_MMPTR(a) (*((volatile uint32_t *)(a)))
```

外设状态会自行变化。`volatile` 告诉编译器这里的访问必须实际发生，不能把第一次读到的按钮状态一直当作常量，也不能删掉看似重复的 LED 写操作。

访问辅助函数还会调用 `csr_io_fence()`。当前源码中这个函数对本章 VexRiscv 配置没有生成实际 fence 指令；不要据此认为每次访问都一定带硬件内存屏障。`volatile` 也不是多核同步机制。

## 5. `character()` 为什么先等 `txfull`？

```c
static void character(char value) {
    while (uart_txfull_read()) {}
    uart_rxtx_write((uint8_t)value);
}
```

UART 的串行发送速度低于 CPU 写字节的速度。LiteX 在中间放了发送 FIFO，默认深度来自 `SoC.add_uart()` 的参数，本章未单独覆盖它。

```text
CPU：写一个字节
       ↓
UART TX FIFO：暂存若干字节
       ↓ 发送器按波特率取走
起始位 0 → 8 个数据位，低位先发 → 停止位 1
       ↓
serial_tx → M11 → Dock USB 桥 → 电脑
```

FIFO 满时继续盲写，不能保证字符都被接收。轮询 `txfull` 是本驱动的背压处理。它会让 CPU 忙等，本章因此简单但并不适合高吞吐应用。

115200 波特率、8N1 下，一个字符占约 10 位，约 86.8 μs；理想上限约 11520 字节/秒。`uart_rxtx_write()` 返回表示这次寄存器写完成，不表示字符已经全部从引脚发完。若要等队列清空，还要理解 `txempty` 的具体语义及串行发送器是否仍在工作。

### 本章为什么有 RX 寄存器，却没写接收程序？

`with_uart=True` 创建了双向 UART，接收引脚和 RX FIFO 都存在。但 `main_tang.c` 只发送日志，没有轮询 `uart_rxempty_read()`，所以电脑输入字符不会自动产生回显。硬件具备接口与软件使用接口是两件事。

如果以后增加接收，在当前默认 RX FIFO 模式下，还要理解“读取”和“消费”之间的区别：

```c
if (!uart_rxempty_read()) {
    uint8_t value = (uint8_t)uart_rxtx_read();
    uart_ev_pending_write(1u << CSR_UART_EV_PENDING_EVENT1_OFFSET);
    /* 再处理 value */
}
```

这里 EVENT1 是当前生成映射中的 RX 事件，偏移 1，所以写入掩码为 2。默认模式下清 RX pending 同时推进 FIFO，后续才能读到下一字节。只不断读 `rxtx`，可能反复看到同一个队首字节。该行为取决于 UART 的 RX FIFO 配置；这里的示意代码没有加入本章固件。

### LED 的 read 函数能证明物理灯亮吗？

`leds_output_read()` 读的是控制寄存器保存的逻辑位，不是光学反馈，也不是自动测量球位电压。写 1 后读到 1 证明寄存器访问这部分；球位约束、反相、连线和物理 LED 还需要对应证据。

## 6. `text()` 和十六进制输出

```c
static void text(const char *value) {
    while (*value) character(*value++);
}
```

字符串以零字符结束。每次取一个字符，指针前移，再交给 `character()`；字符串常量存放在 ROM 中。

`hexadecimal()` 从第 7 个十六进制位打印到第 0 位。每次右移 `4*i`、用 `&15` 提取四位，再查字符表。固定输出八位，是因为这里打印 32 位值；不是 UART 一次发送 32 位字符。

## 7. 按行读 `main()`

```c
uart_ev_enable_write(0);
leds_output_write(LED_MASK);
text("14 HELLO: CPU reached main; LEDs are mapped\r\n");
```

第一行关闭 UART 事件中断，本程序使用轮询。启动代码也关闭全局机器中断，因为本章没有配置完整的中断处理流程。

`LED_MASK` 来自本章生成的 `test_config.h`。默认 `led_count=1`，所以 mask=1。LED5 的硬件输出前取反，因此写逻辑 1 点亮。

HELLO 是“CPU 已执行到 main、经过了 UART 软件和硬件路径”的证据。LED4 硬件心跳没有这层含义。

```c
uint32_t previous = 0xffffffff;
uint32_t alive = 0;
```

`previous` 初始为一个不可能的一位按钮状态，使第一次轮询就打印当前状态。`alive` 是循环计数器，通常由编译器放在寄存器里；不能看到 C 变量就认为必定有对应 RAM 单元。

```c
if (++alive == 1000000u) { /* 打印 ALIVE，然后归零 */ }
```

这里的 1000000 是循环次数。一次循环执行多条指令，还可能等待 UART，故它不是一秒定时器。提高时钟会缩短间隔，但不是精确测频方法。

```c
uint32_t buttons = buttons_input_read();
if (buttons != previous) { /* 打印新状态 */ }
leds_output_write(buttons & LED_MASK);
```

输入是同步后的“按下=1”。软件把低位写给 LED5，于是按住按钮时亮，松开时灭。只有状态变化才打印，避免同一值不断淹没串口。

刚进 main 时写 1，进入循环后又写实际按钮状态；按钮松开时，LED5 很快被写回 0。起始那次点亮可能短到肉眼看不见。

## 8. 为什么需要先生成头文件，再编译 C？

```text
第一遍构造 SoC
    ↓ finalize：确定 CSR 与内存地址
生成 csr.h / soc.h / mem.h
    ↓ GCC 使用这些地址编译 main_tang.c
ELF → 二进制 → ROM 字数组
    ↓ 第二遍用相同配置构造 SoC
输出含真实程序初值的 RTL
```

第一遍传入 `[0x0000006f]`，即一条原地跳转指令，用来提供临时 ROM 内容。这一遍的任务是生成软件需要的接口，不是交付实际功能程序。

`compile_software=False` 表示 Builder 不替我们编译软件；本章自己调用 `firmware()`。`compile_gateware=False`、`run=False` 表示本阶段生成构建输入，没有完成 FPGA 综合/布局布线。

## 9. GCC 的选项为什么这样选？

| 选项 | 本章用途 |
| --- | --- |
| `-march=rv32im` | 指令集必须能被当前 CPU 配置执行 |
| `-mabi=ilp32` | 使用 32 位整数/长整数/指针的 ABI |
| `-mno-relax` | 禁止此构建中的链接松弛，保持最小启动方案可控 |
| `-O1` | 做基本优化，因此短访问函数可能被内联 |
| `-ffreestanding` | 程序不运行在普通宿主系统环境里 |
| `-fno-builtin` | 不依赖编译器对标准库函数的内建替换 |
| `-nostdlib -nostartfiles` | 不引入默认 C 运行库/启动文件，使用我们的 `_start` |
| `-I .../generated` 的父级目录 | 找到 `generated/csr.h` 等硬件接口 |
| `-Wl,-T,linker.ld` | 把链接地址交给本章脚本规定 |
| `-Wl,-Map,program.map` | 留下各区段、符号位置的记录 |

工具名虽然是 `riscv64-unknown-elf-gcc`，本次 `-march`/`-mabi` 明确要求生成 32 位程序。不能只看工具名判断输出位宽。

## 10. 链接脚本把什么放在哪里？

```text
ROM，0x00000000，默认 8 KiB
  .text：_start 与 C 函数指令
  .rodata：字符串等常量
  .data 的初始化镜像（若存在）

main_ram，0x40000000，默认 16 KiB
  .data：有初值变量的运行位置
  .bss：应当清零的变量
  ... 可用空间 ...
  0x40003c00：本章预留栈预算的下界
  ... 1024 字节栈预算 ...
  0x40004000：初始 sp，向低地址分配
```

`ENTRY(_start)` 设置 ELF 的入口信息；CPU 的复位 PC 由硬件参数设置。这里两者匹配，但并不是 ELF 会自动替 FPGA 修改复位入口。

`KEEP(*(.text.init))` 将启动代码放在 `.text` 开头。`.data > main_ram AT > rom` 区分运行地址和加载地址。`LOADADDR(.data)` 给启动代码 ROM 侧地址。

`.bss(NOLOAD)` 不需要在镜像里保存一大段零；启动代码负责清它。

`ASSERT(__bss_end <= __stack_bottom)` 检查静态变量没有侵入预留栈空间。它没有测量运行时的最深调用，也不会给 CPU 设置栈界限保护。

默认本次 `program.map` 中 `.data` 和 `.bss` 长度都为 0：程序的局部状态主要在寄存器/栈里。复制和清零循环仍保留，便于以后加入全局变量；本程序会直接跳过空区段。

## 11. `_start` 怎样把 C 运行条件准备好？

1. `la sp, __stack_top`：初始 sp 指向 RAM 高端。一旦函数分配栈帧，sp 向低地址移动。
2. `csrci mstatus, 8`：关闭全局机器中断。
3. 用 `lw` 从 ROM 加载 `.data` 的一个字，用 `sw` 写入 RAM；两个指针都加 4，直到运行区结束。
4. 用 `sw zero` 每次清 `.bss` 的一个字。
5. `call main`：调用 C 入口，设置返回地址 ra。
6. 如果 main 返回，原地循环，避免执行到不相关数据。

本次实际反汇编里，main 在地址 `0x90`，入口执行 `addi sp,sp,-48`：它为保存 ra、若干寄存器分配 48 字节栈帧，sp 从 `0x40004000` 变为 `0x40003fd0`。这是这次编译结果，不是所有 main 都用 48 字节。

## 12. 函数调用最终真的成了 load/store 吗？

当前 ELF 中，`text()` 的发送循环包含：

```asm
lui  a3, 0xf0000       # a3 = 0xf0000000
lw   a4, 4(a3)        # 读 UART txfull
bnez a4, ...          # 满则继续等待
sw   a5, 0(a3)        # 写 UART rxtx
```

C 的短函数已经被内联。反汇编里找不到一个独立的 `uart_rxtx_write` 函数，并不表示访问不存在。

## 13. ELF 如何进入 FPGA 的 ROM？

```text
program.elf：指令、区段、符号、入口信息
      ↓ objcopy -O binary
program.bin：按加载布局提取的原始字节
      ↓ 检查不超过 rom_size，填充到 ROM 容量
每四个字节按 little endian 拼一个 Python 整数
      ↓ integrated_rom_init
tutorial14_rom.init：每行一个 32 位字
      ↓ Verilog Memory 初值 / 综合工具
FPGA 块存储初始内容
```

默认 ROM 第一行是 `40004117`，原始字节顺序是 `17 41 00 40`。反汇编显示它是启动代码的 `auipc sp,0x40004`。镜像里的字节顺序、CPU 小端取数与 ROM 字数组必须一致。

这一步没有通过 UART 把 C 程序上传到 CPU。固件已经成为 FPGA 配置中的存储初值；修改 C 后要重新编译固件、重新生成 ROM，再完成后续构建和下载。
