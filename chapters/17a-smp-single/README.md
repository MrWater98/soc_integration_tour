# 17A：先让 SMP 核心只运行一个 hart

第 17 章使用普通 `vexriscv`。本章换成 LiteX 的另一个原生集成 `vexriscv_smp`，先设置 `cpu_count=1`。这样可以先解决接口变化，再进入双核。

**目前交付是实际 CPU RTL 仿真，尚未综合或下载这个 SMP 版本。** 普通 VexRiscv 的板上结果不能算作本章通过。

## 1. 为什么一个核也要单独做一章？

`hart` 是 RISC-V 对一个硬件执行线程的称呼。本章一个 hart 独立运行程序；下一章两个 hart 分别有自己的 PC、寄存器和栈。

CPU 类型变化后，中断和缓存的接口也变化：

```text
17 普通 VexRiscv                 17A VexRiscv-SMP，1 hart
CPU → Wishbone → ROM/RAM/CSR     hart0 → 缓存/集群 → Wishbone → ROM/RAM/CSR
CPU 专用中断掩码                CLINT：软件中断、计时器
                                PLIC：外部中断控制器
```

CLINT、PLIC 在 SMP 核心内实现，LiteX 把它们的访问接口接入 SoC 地址图。本章实测的是 **CLINT 软件中断和定时器中断**；PLIC 外部中断仍需后续用例；本章同时检查 CLINT 定时器中断。它们出现在地址图中不代表功能都已验证。

## 2. 用什么配置？

| 配置 | 本章值及来源 |
| --- | --- |
| CPU 集成 | `vexriscv_smp`，`standard` |
| hart 数 | 本章固定 1，用作单核对照 |
| 指令/数据缓存 | 各 4 KiB、1 路，选用已有匹配 RTL |
| 缓存接口宽度 | 32 位，本章配置 |
| 主 RAM | 64 KiB，映射在 `0x40000000` |
| ROM | 8 KiB，复位入口为 0 |
| CLINT / PLIC | 当前 LiteX 集成的默认地址 `0xf0010000` / `0xf0c00000` |
| 时钟 | 仿真理想 1 MHz；不是板上时钟或 Fmax |
| UART | 仿真 100000 波特率，8N1；每位正好 10 个系统周期 |
| ISA | 固件编译为 RV32IMA，包含原子指令 |

`run.py` 明确设置 CPU 类参数；这里没有调用多核命令行默认值推导。选定配置匹配已安装的 `pythondata_cpu_vexriscv_smp` 预生成 RTL。缺少匹配文件时，LiteX 会尝试用 SBT 生成，须准备相应 Scala/Java 依赖。

## 3. 一次执行如何发生？

```text
Python 设置 CPU、ROM、RAM、UART
              ↓
LiteX finalize → 分配 CSR 地址 → 生成 csr.h
              ↓
GCC 编译本章 startup.S 和 main.c → ROM 字数组
              ↓
重新生成同一 SoC → 顶层 RTL + CPU RTL + RAM 模块 + 初值
              ↓
Verilator：释放复位 → PC=0 → 设置 sp、mtvec → main(hartid)
              ↓
RAM 检查 → CLINT 软件中断 → 原子加法 → 邮箱检查
              ↓
真实 UART TX 位流 → 测试台解码 → 主机核对日志
```

本章程序没有 `.data`、`.bss` 对象；链接脚本断言这两个区段为空。共享测试区由 hart0 显式初始化。若扩展程序引入初始化变量，就需要加入 `.data` 拷贝与 `.bss` 清零，不能直接套用这个最小启动代码。

## 4. 具体检查什么？

1. CPU 读取 `mhartid`，必须是 0。
2. 在本 hart 的 512 字测试区写入与下标相关的模式，再逐字核对。
3. 对一个字执行字节写，验证 `0x11223344` 变为 `0x1122aa44`。
4. CPU 设置 CLINT 的本 hart `msip`，硬件进入 trap；处理程序核对 `mcause=0x80000003`，清 `msip` 并增加软件计数。主程序重复发起 3 次独立请求，最终核对计数为 3。
5. 用稳定的高/低字读取 `mtime`，把本 hart 的 `mtimecmp` 设置到未来时刻；启用机器定时器中断，处理程序核对 cause、禁用本次比较并增加计数。最终要求每 hart 恰好一次。
6. 默认做 1000 次 `amoadd.w.aqrl`，检查共享计数为 1000。
7. 邮箱记录 hart 编号、迭代数、求和结果和完成标记；主机核对实际数值。
8. 测试台再次施加系统复位，要求整套程序再次通过；默认 2 次运行。

1000、512、64 KiB 都是本实验选择。`--work`、`--reboots` 可以调整；测试区大小与内存/栈布局目前写在本章实现中，调整时应一起审核。

## 5. 运行与结果

从仓库根目录：

```bash
python chapters/17a-smp-single/run.py
python chapters/17a-smp-single/run.py --work 257 --reboots 3 \
  --output results/17a-parameters
```

依赖：第 00 章的 LiteX/Migen、RISC-V GCC、Verilator、支持 C++20 的编译器，以及 SMP CPU 数据包。所有实验逻辑都在本章，只共用根目录的路径定位函数。

默认结果应包含：

```text
SMP HART 00000000 count=000003E8 sum=0007A314
SMP ATOMIC count=000003E8
SMP IRQ PASS
SMP TIMER PASS
SMP PASS harts=00000001
```

主机不只寻找 PASS：还核对 hart 编号、次数、求和值、原子总数以及复位次数。

| 产物 | 如何看 |
| --- | --- |
| `results/17a/rtl/` | 全部 CPU、顶层、通用缓存 RAM、ROM/RAM 初值和测试台；`sources.json` 保存哈希 |
| `builder/csr.csv` | 新集成的地址图，尤其 CLINT、PLIC 与 UART |
| `firmware/` | ELF、链接图、二进制、编译日志 |
| `run.log` / `summary.json` | 实际串口解码、执行结果与编译/运行耗时 |

当前对照覆盖启动、RAM/字节写、UART、软件/定时器中断和原子指令。第 17 章的随机 UART 双向回显、外部 Timer/PLIC IRQ 压力以及长时间板上运行尚未迁入 SMP 版本；不能称为完整等价回归。FPGA 资源和时序也要综合后再比较。
