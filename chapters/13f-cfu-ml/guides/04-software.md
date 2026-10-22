# 4. 从main.c到一条真实的CUSTOM0指令

打开[main.c](../main.c)。以下按程序执行顺序读，打包细节已在[数据篇](02-data.md)逐行解释。

## 4.1 头文件与观察接口

```c
#include <stdint.h>
#include "cfu.h"
```

第一行提供uint8_t/int8_t/uint32_t等确定位宽类型。第二行使用原版CFU Playground头文件；编译命令中的-I upstream让编译器找到它。

```c
#define TRACE(n) (*(volatile uint32_t *)(0x80000000u+4u*(n)))
```

这是本章的日志端点：n选择一个32位字，地址每次增加4字节。volatile要求保留真实内存访问；指针解引用在CPU上成为store指令。它经过Wishbone去日志端点，**不是CFU操作本身**。

## 4.2 普通C参考计算为什么保留？

```c
__attribute__((noinline)) static int32_t reference_dot(
    const volatile uint8_t *x, const volatile int8_t *w, unsigned n)
```

noinline要求编译器保留函数调用；const表示本函数不通过指针修改元素；volatile要求每次读数组都实际执行，避免计时循环的相同计算被移出循环。输入无符号8位，权重有符号8位；n是元素个数。

参考路径逐个读取元素、做普通乘加，不读取CFU的内部结果。它是对拍基准，也是本次CPU基线。

```c
static volatile int32_t sink;
```

每次计时循环都把结果写入这个变量，防止整个无用计算被删除。这次测量包含这次共同的结果写入成本。

## 4.3 accelerated_dot逐行读

```c
cfu_op0(1,0,0);
```

三个参数分别是funct7、两个操作数。cfu_op0中的0选funct3=0；第一参数1选funct7=1，令硬件清累加器。两份操作数0在这个清零操作中不参与运算。

每次新点积必须先清零；否则上一次输出神经元的和会混进下一次结果。

```c
uint32_t result=0;
for(unsigned i=0;i<n;i+=4) {
```

初始化软件接收结果，每次处理四项。这里i是元素索引，前进4个元素；不是对Wishbone地址加4字节。

```c
unsigned remaining=n-i;
if(remaining>4) remaining=4;
```

求当前这组有效元素数，最多4个。长度17时，最后一组只有1个有效元素；其余由打包函数补齐。

```c
result=cfu_op0(0,pack_inputs(x+i,remaining),pack_weights(w+i,remaining));
```

先读并打包当前四个输入/权重，形成两个32位值；funct7=0表示执行乘加并累加；CPU执行自定义指令，等待硬件响应，再把返回值赋给result。

8项输入会发两条累加命令：第一次返回前四项和，第二次返回八项总和。因此不需要另加一条“读取累加器”的命令。

```c
return (int32_t)result;
```

把返回位模式按32位有符号数解释。它可能是负点积，不应因为接口类型uint32_t就当成很大的正数。

## 4.4 cfu_op0怎么变成机器指令？

沿原版[cfu.h](../upstream/cfu.h)看宏展开：

```text
cfu_op0(0,a,b)
  → cfu_op(0,0,a,b)
  → cfu_op_hw(0,0,a,b)
  → opcode_R(CUSTOM0,0,0,a,b)
  → 内联汇编用.word编码一条32位机器指令
```

R型字段是：

```text
31        25 24    20 19    15 14   12 11     7 6        0
┌──────────┬────────┬────────┬───────┬─────────┬──────────┐
│ funct7   │ rs2    │ rs1    │funct3 │ rd      │ opcode   │
│ 操作类别 │ 输入1  │ 输入0  │低功能位│ 结果寄存器│ 0x0b    │
└──────────┴────────┴────────┴───────┴─────────┴──────────┘
```

rs1/rs2字段是寄存器编号，不是直接把32位数据塞进指令。CPU先根据这些编号取到寄存器中的数据，交给CFU。

[上游riscv.h](../upstream/riscv.h)中的opcode_R用移位和按位或，将这些字段放进32位字。`asm volatile`要求保留该自定义操作；输入约束"r"让GCC安排寄存器；输出"=r"告诉GCC目标寄存器接收结果。

本次反汇编中有一条：

```text
1a4: 00a4850b  0xa4850b
```

拆开0x00a4850b：opcode=0x0b，funct7=0，funct3=0，rs1=x9、rs2=x10、rd=x10。意思是拿x9/x10的值执行MAC，把结果放回x10。目标可以和源寄存器相同，CPU会先读取旧操作数再写回。

这里objdump只显示十六进制，因为标准反汇编器不知道本项目自定义语义；不意味着没有生成指令。run.py通过最低7位为0x0b识别实际.text中的CUSTOM0。

funct7=1清零的例子在地址0x164，机器码0x02f7878b。地址和寄存器分配是当前编译结果，改源码、优化或工具版本后可能变化。

## 4.5 main的四个检查阶段

### 第一阶段：一个点积

先算4项，要求结果13，还要与reference_dot一致，再向TRACE(1)写结果。这就是学习起点，不要求先看完整模型。

### 第二阶段：两个输出神经元

output循环两次，每次换一行权重。CFU算点积；CPU加bias并执行ReLU。除与参考比较外，还显式检查结果28和0，避免两条错误路径碰巧算出同一个错误值。

### 第三阶段：长度与数值变化

xorshift随机数状态用固定seed初始化。64组测试长度依次取1～17并重复，包含不足4、刚好4、超过4以及最后余1的情况。每组独立清累加器，再与普通C比较。

64是本章测试数量，不是穷举。权重使用当前RISC-V GCC的int8_t二补码转换；输入按uint8_t截取。

### 第四阶段：计时

```c
uint32_t start=cycles();
...
uint32_t elapsed=cycles()-start;
```

cycles用rdcycle读取CPU周期计数低32位。差值是这段代码消耗的模拟CPU周期；不是主机运行Python的毫秒数。当前片段足够短，不跨越完整32位计数范围。

cycles里的内联汇编还带有`"memory"` clobber：告诉编译器不要把内存访问随意移过计时边界。它是编译器约束，不是给硬件发了一条内存fence。

预打包计时前还有：

```c
__asm__ volatile("" : "+r"(a0), "+r"(b0), "+r"(a1), "+r"(b1) :: "memory");
```

空字符串不生成机器指令；四个`+r`约束让打包值先准备在寄存器中，并告诉编译器这一步会读写这些寄存器值，防止把未完成的打包计算挪进后面的计时循环。

测三种路径：普通C；每次读数组并打包的CFU；已经准备好四个操作数word、只测clear和两条MAC的CFU。第三种的打包在计时之前，必须在报告中单独写明。

## 4.6 相同代码怎样切换到软件模拟？

编译时定义CFU_SOFTWARE_DEFINED，原版cfu.h就将cfu_op改为software_cfu函数调用，不生成CUSTOM0。

本地[software_cfu.c](../software_cfu.c)模拟实际核心：

```c
static uint32_t accumulator;
```

跨函数调用保留累加状态，启动时属于.bss，需要startup.S清零。

```c
return value<128 ? (int)value : (int)value-256;
```

从字节位模式恢复有符号值，与Verilog$signed含义对应。

```c
if(funct7) accumulator=0;
```

匹配上游“非零funct7都清零”的行为，而不是只支持1。

```c
accumulator+=(uint32_t)((signed_byte(a,lane)+128)*signed_byte(b,lane));
```

按四个lane分别计算；将乘积转无符号后累加，以定义良好的模2^32算术模拟硬件低32位行为。

上游dse_template/src/software_cfu.cc仍是rs1+rs2示例，和此MAC不等价，所以我们没有用它当正确答案。数学参考仍然是独立的reference_dot；本地软件模拟只是额外一条对照路径。

软件模式的CPU与硬件连接不变，但不执行自定义指令。日志必须显示commands=0，反汇编也必须没有CUSTOM0；这比“代码里有cfu_op名字”更能证明实际选择的路径。

## 4.7 startup.S、linker.ld在这章仍然干什么？

本章携带自己的启动和链接脚本。_start设置SP、把.data初值从ROM复制到main RAM、清.bss，然后call main。CFU不会替你初始化C的全局变量或创建栈。

linker.ld中的MAIN_RAM_LENGTH由编译命令设为16384，与SoC的16KiB main RAM一致。4KiBROM容量在编译后检查；镜像再填到完整1024个32位字，交给LiteX ROM初始化。
