# 第 08 章：通过 CSR 控制 GPIO，并读回外部输入

本章让 CPU 使用 C 代码控制 4 个输出脚，再读取 4 个输入脚。这个 4+4 是实验选择，不是 GPIO 的固定形式：实际 SoC 可以按需要配置位数和方向。这里用 4 位便于同时观察 `0xa`（`1010`）输出和 `0x5`（`0101`）输入。外部输入由仿真器在指定时刻从 `0000` 变成 `0101`，读输入只能观察引脚，不能把输入状态写成想要的值。

## 输入

- 本章自己的 [`soc.py`](soc.py)、[`startup.S`](startup.S)、[`linker.ld`](linker.ld) 和 [`main.c`](main.c)；运行器只读取本章的这些实验源文件，并使用 RISC-V C 工具链。
- 本章自己的 [`litex_builder.py`](litex_builder.py) 负责 LiteX SoC 构建与仿真。
- LiteX Builder 为当前 SoC 生成的 `csr.csv` 与 `generated/csr.h`。
- 仿真平台上的 4 位 `gpio_in`、4 位 `gpio_out`；`gpio_in` 在第 1000 个 `sys` 时钟后从 `0x0` 变为 `0x5`，且保持该值。

## 概念速查

| 名词 | 好记的一句话 | 本章观察位置 |
| --- | --- | --- |
| GPIO | CPU 可读写的通用数字输入/输出脚 | `GPIO_OUTPUT` 日志与仿真 pins |
| CSR | 用来配置外设或读取外设状态的小寄存器 | `csr.csv` 与 `generated/csr.h` |
| CSRStorage | CPU 可写、硬件可读的寄存器，例如输出控制值 | `gpio_out_output_write(0xa)` |
| CSRStatus | 硬件提供状态、CPU 读取的只读寄存器 | `gpio_in_input_read()` |
| CSR bridge | 把 CPU Wishbone 访问转成 LiteX CSR 总线访问 | `csr_bridge` 与 `csr_interconnect` 层级 |
| MultiReg | 用两级触发器降低异步输入造成亚稳态传播的风险 | `GPIOInput` 的 `MultiReg(pads, ...)` |
| 地址映射 | 把 CSR 名称变成 CPU 可访问的地址 | `results/08/memory_map.csv`、`csr.csv` |
| 同步器 | 在本地时钟沿采样外部输入 | 仿真输入变化后 CPU 稍后读到 `0x5` |

## 一次 GPIO 读写经过什么

```text
C 调用 gpio_out_output_write(0xa)
       │ 写 CSR 地址（普通 CPU store）
       ▼
VexRiscv dbus Wishbone → LiteX 地址译码 → CSR bridge → CSRStorage
                                                │
                                                └──> gpio_out[3:0] = 1010

仿真输入 gpio_in[3:0] = 0101 → MultiReg 两级同步 → CSRStatus
                                                         │
C 调用 gpio_in_input_read() <── CSR bridge / Wishbone ───┘
```

CPU 发起写入，CSRStorage 保存输出值，外设逻辑把它送到输出脚。输入方向则相反：仿真/板外信号进入同步器，CSRStatus 提供给 CPU 读取。输入 CSR 是只读的；软件不能用 `gpio_in_input_write()` 改变真实输入脚。

本章使用明确命名的 `CSRStatus` 与 `CSRStorage` 写出 GPIO 的最小内部结构，并用 `MultiReg` 做输入同步。它们分别对应 LiteX 常见的 `GPIOIn` 和 `GPIOOut` 功能；显式 CSR 名称也让生成的 C API 在当前 LiteX/Python 组合中稳定可见。

本章新增两个 CSR bank 后，生成的地址顺序也变了。查 `csr.csv` 时区分 bank 起点（`csr_base`）和具体寄存器（`csr_register`）：

| CSR 寄存器 | 字节地址 | 方向 | C 程序的动作 |
| --- | ---: | --- | --- |
| `gpio_in_input` | `0xf0000000` | `ro` | 轮询读 |
| `gpio_out_output` | `0xf0000800` | `rw` | 写 `0x0`、`0xa` |

06/07 章的 `identifier_mem` 在 `0xf0000000`；加入 GPIO 后它移到 `0xf0001000`。因此外设一变，软件就应重新使用本章生成的 `csr.h`，不能沿用上章的地址常量。

## 参数和最小程序

| 参数 | 值 | 作用 |
| --- | ---: | --- |
| 输入/输出位宽 | 各 4 bit | 只保留低四位供学生观察 |
| 输出复位值 | `0x0` | 仿真开始时四个输出为低 |
| 输入初值/变化值 | `0x0` → `0x5` | 变化后按位为 `0101` |
| 仿真输入变化时刻 | 第 1000 个 `sys` 时钟沿，之后保持 | 让 CPU 先读到 0，再看到外部变化 |
| 输入同步 | 两级 MultiReg | CPU 读取的是同步后的状态 |
| CPU 成功条件 | 先读到 `0x0`，再读到 `0x5`，只读写入试验后仍为 `0x5` | 输入变化必须被 CPU 确实观察到 |

[`main.c`](main.c) 先写输出 `0x0` 再写 `0xa`，然后轮询输入 CSR；先读到 `0x0` 时向测试探针写 0，后来读到 `0x5` 时写 5。随后故意通过生成的地址宏对只读输入 CSR 发一次原始写，再读回确认仍为 `0x5`。只有这个检查也通过才向完成端点写成功码。运行器先用同一硬件参数让 Builder 分别生成 CSR 头文件和地址图，再交叉编译 C 固件，最后以编好的 ROM 镜像重建同一 SoC；两次生成的地址图均被核对，因此 C 函数名与硬件寄存器保持一致。

## 常见问题

### 本章 GPIO 实验依赖哪些 SoC 配置？

`SoCCore` 保留 4 KiB ROM、4 KiB 集成 SRAM 和 16 KiB main RAM，供裸机 C 镜像与运行时使用，同时关闭默认 UART、Timer 和控制器。GPIO bank 是本章自己写的 CSR 模块，不是 LiteX 的 `GPIOIn` / `GPIOOut` 实例：`GPIOInput` 用 `CSRStatus(4)` 暴露输入，并用两级 `MultiReg` 同步；`GPIOOutput` 用 `CSRStorage(4, reset=0)` 保存输出值，再直接驱动引脚。这里的位宽和复位值配置的是 GPIO 引脚组，不是内存区域。

新增 CSR bank 会改变 CSR 地址分配；bank 名和寄存器名也会成为软件接口的一部分。模块名、显式 CSR 名称、生成的 `csr.h` 和固件必须来自同一份 SoC 配置。修改 `csr_paging` 或再增加一个 CSR bank，都可能移动后续 bank 地址；固件应使用新生成的头文件，不要手写并沿用旧地址。

第 1000 个 `sys` 时钟后改变输入，只是仿真激励选择的时刻，不是 GPIO 必须等待的时间，也不是同步器固定延迟。输入何时被本地逻辑看见由两级 `MultiReg` 决定；若把激励提前或推后，要确认 CPU 轮询仍能先读到初值、再读到变化后的值，事件顺序检查也仍然成立。

### CSR 是什么，C 代码怎么访问？

CSR 是映射到 CPU 地址空间的一组小型控制/状态寄存器。LiteX Builder 分配寄存器地址并生成 `generated/csr.h`，头文件里的 `gpio_out_output_write()` 和 `gpio_in_input_read()` 最后会变成 CPU 的 load/store，再经 CSR bridge 到达外设。GPIO 不是直接连到 C 变量。

### 为什么输入 CSR 只能读？

输入状态来自引脚。软件可以采样，不能靠写寄存器改变外部输入。本程序故意对生成地址做一次原始写，再读回来，必须仍为 `0x5`。这可以排除“软件把想要的值写进去，再假装从输入读到”的假成功。

### `MultiReg` 有什么作用？

仿真输入引脚相对本地逻辑是外部信号。`MultiReg` 用两个本地时钟级采样，降低亚稳态传播的风险；CPU 读到同步后的值会比 pad 变化晚几个周期。本实验展示信号路径，不代替板级 CDC 和电气检查。

### 为什么编译 C 之前要先生成 `csr.h`？

增加 CSR bank 会改变 CSR 地址分配。本章生成的 `gpio_in_input` 位于 `0xf0000000`，`gpio_out_output` 位于 `0xf0000800`；新增 bank 后 identifier CSR 也发生移动。运行器先生成并检查本章 `csr.csv` 和 `csr.h`，再用该头文件编译 C；最终 SoC 再次生成并核对相同地址，避免固件沿用旧常量。

### 日志怎样证明 CPU 看到了输入变化？

`GPIO_INPUT_DRIVE value=0x5` 是仿真环境改变引脚的记录。前后的 `SOC_PROBE data=0x00000000` 和 `SOC_PROBE data=0x00000005` 是 CPU 读完输入后主动写入的观察值。运行器检查事件顺序，并确认输出有 `0→a` 变化。只看最终值无法证明 CPU 先读到 0、后来读到新值。

## 运行、输出与验证
构建时使用的 Verilog 输入会复制到 [`results/08/rtl`](../../results/08/rtl)，包括 SoC 顶层、Vex CPU、RAM 支持模块、ROM/RAM 初始化文件和源清单。

```sh
python3 chapters/08-gpio/run.py
```

预期 `memory_map.csv` 中 `gpio_in_input` 为 `0xf0000000,ro`，`gpio_out_output` 为 `0xf0000800,rw`。运行器按顺序检查以下真实日志事件，最后显示 `PASS 08-GPIO`：

```text
GPIO_OUTPUT value=0xa
SOC_PROBE data=0x00000000
GPIO_INPUT_DRIVE value=0x5
SOC_PROBE data=0x00000005
SOC_COMPLETE word_address=0x200003ff data=0x0000005a sel=f
```

输出日志可能在复位阶段重复记录 0；运行器要求它最终只发生一次 `0→a` 变化。两个 `SOC_PROBE` 是 CPU 在读到输入 0 和 5 后主动写出的观察记录；中间的 `GPIO_INPUT_DRIVE` 是仿真环境驱动 pad 的记录。它们有顺序约束，故不能只凭一次最终读数判定输入变化已被 CPU 看到。检查以下文件：

| 文件 | 看什么 |
| --- | --- |
| `results/08/builder/csr.csv` | `gpio_in` 与 `gpio_out` CSR base 和 `0xf0000000` CSR 区 |
| `results/08/csr-header.txt` | 自动生成的 CSR 名称、读写函数与地址宏 |
| `results/08/firmware/program.map`、`disassembly.txt` | C 函数被放进 ROM，CSR 读写最终是内存映射 load/store |
| `results/08/memory_map.csv` | Builder 导出的本章地址图副本 |
| `results/08/irq_map.csv` | 只有表头；GPIO 本章用轮询，未配置中断 |
| `results/08/build.log`、`compile.log` | SoC 构建与仿真器编译过程 |
| `results/08/run.log`、`builder/gateware/sim.vcd` | 引脚变化、CPU 读写、成功完成的证据 |

波形里把 `gpio_in`、`gpio_out` 和 CSR bus 请求对应起来：输入值变化后先经过两个时钟采样级，再由 CPU 轮询读到；输出值从 0 变成 A。若生成的 `csr.h` 没有 `gpio_in_input_read` / `gpio_out_output_write`，说明 C 固件和 CSR 模块命名没对上，不能跳过直接假设读写成功。

## 故障检查与下一步

- `csr.csv` 中没有 GPIO：检查两个 GPIO 模块是否作为 SoC 子模块加入，并重新运行 Builder。
- 输出日志没有 `0xa`：检查 `gpio_out_output_write()` 与 output pads 的连接及输出 CSR 地址。
- 输入一直是 0：检查仿真输入激励、`MultiReg` 时钟和输入 CSR；读取状态的 C 函数必须与 `csr.h` 相符。
- 写输入 CSR 不会改变输入脚：这是预期设计。输入状态来自物理 pad；本章在日志 PASS 前还会验证一次原始写入后读数仍为 `0x5`。

进入下一章前，能从自动生成头文件找到两个函数对应地址，说明输出写入和输入读取经过的模块，并用仿真证据证明两者都成功。

## 本章速记

1. GPIO 外设通过 CSR 暴露给 CPU；CSR 地址由 LiteX Builder 统一生成。
2. 输出是 CPU 写 `CSRStorage`，输入是硬件写 `CSRStatus`、CPU 只读。
3. 外部输入先经同步器再供 CPU 读取；CPU 读到的是同步后的采样值。
4. `csr.h` 连接软件函数和硬件 CSR；CPU 写输出、读输入、写完成码构成端到端证据。
