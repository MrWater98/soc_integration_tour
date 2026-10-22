# 13D：先会用 GDB，再理解芯片调试

## 这一章为什么先调试本机程序？

前面已经把外部命令送进 TAP。现在增加软件视角：我们想让程序停在哪里？停下后观察什么？一步执行到底是什么？

GDB 是程序调试器。我们先用真实 GDB 调试本机的递归阶乘，再把后端换成芯片的路径画清楚。这个实验不需要 OpenOCD，也不经 JTAG；目标 CPU 是你的宿主机。

```text
本章：GDB --> 操作系统的进程调试接口 --> 本机 C 程序
未来：GDB --> OpenOCD --> JTAG 适配器 --> 芯片调试模块 --> SoC CPU
             ^                                        ^
             软件换后端                     硬件要提供停机、寄存器访问等能力
```

## 先运行完整实验

依赖 Python、GCC、GDB：

```bash
python chapters/13d-gdb/run.py
```

输出 `results/13d/gdb.log`、`summary.json` 和 `REPORT.md`。本章没有被测 RTL，调试输入是 `fact.c` 与 `session.gdb`，两者会复制到结果目录，不需要制造一个空的 `rtl/`。

编译使用 `-g -O0`、保留帧指针并关闭尾调用优化，让源码与递归调用比较好观察。这些是教学编译选项；优化后的程序可能有内联、变量消失、栈帧合并。

## 实验一：断点不是结束程序

```c
int fact(int n) {
    if (n <= 1) return 1;
    int child = fact(n - 1);
    return n * child;
}
```

在函数入口设断点，然后启动程序：

```gdb
break fact
run
print n
```

第一次停在 `fact(3)`。函数还没结束，只是执行被暂停，方便我们观察。`continue` 后，下一次调用 `fact(2)` 又会碰到这个断点，再继续会停在 `fact(1)`。

```text
main --> fact(3) [停] --> fact(2) [停] --> fact(1) [停]
              continue          continue
```

日志中的 `FRAME_N=3、2、1` 是每次停下后真正读取参数得到的，不是脚本预先打印的期望。

## 实验二：看 PC、SP 与调用栈

```gdb
print/x $pc
print/x $sp
backtrace
```

PC 是下一步执行位置。SP 是当前分配栈空间的边界，不是函数代码地址。递归进入更深一层，函数序言会分配新的栈帧；返回时释放它。地址会因架构、编译器和运行环境变化，不应背一个固定值。

在 `fact(1)` 停下时，`backtrace` 展示：

```text
#0 fact(1)   <-- 现在停在这里
#1 fact(2)   <-- 等待 child 的结果
#2 fact(3)   <-- 等待 child 的结果
#3 main      <-- 等待 fact(3) 的结果
```

这是 GDB 根据目标状态和调试信息重建的调用关系。[GDB 调用栈说明](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Backtrace.html)

本机验证的 x86_64 日志中，五次 SP 相对第一次停在 `fact(3)` 的偏移为 `0、-48、-96、-48、0` 字节：进入时分配、返回时恢复。48 字节来自本次编译的栈帧布局，并非函数调用固定需要的大小；你运行时以自己的日志为准。自动检查会确认三层 SP 不同，返回后恢复到对应调用者的 SP。

本机若是 x86，返回地址的保存机制与 RISC-V 的 `ra` 不同，不要寻找一个必然存在的 `$ra`。SoC 用 RISC-V 时，再观察 `ra`、函数序言里的保存与恢复。

## 实验三：step、next、finish 怎么选？

| 操作 | 想做什么 |
| --- | --- |
| `step` | 推进一个源码步骤，遇到可调试函数调用可以进入 |
| `next` | 推进一个源码步骤，通常越过函数调用；其他断点仍可能打断 |
| `stepi` | 推进一条机器指令 |
| `finish` | 运行到当前函数返回；其他停止事件仍可能打断 |
| `continue` | 继续运行到下一个停止事件或程序结束 |

源码一行可能对应多条机器指令，`step` 不等于一个时钟周期。[GDB 执行与步进说明](https://www.sourceware.org/gdb/current/onlinedocs/gdb.html/Continuing-and-Stepping.html)

自动实验实际使用 `step`，在最内层用两次 `finish`，分别返回 `fact(2)`、`fact(3)`，最后 `continue`，检查 `fact(3)=6`。`next` 与 `stepi` 留给下面的交互操作。

## 亲自敲一遍

自动运行以后，在教程根目录：

```bash
gdb -q results/13d/fact
```

依次输入：

```gdb
break fact
run
print n
print/x $pc
print/x $sp
step
next
continue
backtrace
disassemble fact
stepi
quit
```

每次观察当前源码行和变量再继续。要从头重来用 `run`；查看栈帧用 `frame 1`，再 `print n`，这时看到的是调用者那一层的参数。

## 怎样才能换成我们真正的 SoC？

现在有两块分别验证过的能力：13C 的 TAP 访问，以及本章的调试操作。中间还缺 CPU 调试硬件：

```text
GDB 的“停机”请求
   --> OpenOCD 按具体目标编码
   --> 调试传输入口
   --> Debug Module 通知 CPU
   --> CPU 到达允许停机的状态，保存调试 PC
   --> 模块返回完成，GDB 读取寄存器
```

RISC-V 标准架构中，JTAG DTM 通过 DMI 访问 Debug Module；模块与 CPU 协作处理停机、恢复与寄存器访问。[RISC-V 调试规范](https://docs.riscv.org/reference/debug/v1.0/debug_module.html)

集成时要逐项验收：核的调试配置与生成 RTL、系统复位与调试复位、TCK 跨时钟交接、OpenOCD 目标支持、匹配固件的 ELF、停机/读 PC/单步/恢复行为。当前 VexRiscv standard 教学系统没有这条已验证通路，不能直接把标准 RISC-V DTM 图当成现有 VexRiscv 调试实现。

Tang 板卡下载 FPGA 所用的 JTAG 配置入口也不会自动成为 CPU 调试入口。上板之前，先完成这四章的电脑实验；板卡到货后按第 16 章识别与下载步骤操作。
