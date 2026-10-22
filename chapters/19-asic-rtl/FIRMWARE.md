# 固件为什么这么写：把启动、内存和中断连起来

本章保留07章的启动结构，但RAM缩小为默认2KiB，新增真正的Timer中断。先看[main.c](main.c)，再对照[startup.S](startup.S)和[linker.ld](linker.ld)。

## 地址表先看明白

```c
#define REG(n) (*(volatile uint32_t *)(0x80000000u + 4u*(n)))
```

逐层展开：0x80000000是本地寄存器窗口基址；n是寄存器编号；每个32位寄存器占4字节，所以加4×n；强制转换成32位指针；`*`执行访问；volatile要求编译器保留实际读写。

| n | 字节地址 | 读/写含义 |
| --- | --- | --- |
| 0 | 0x80000000 | 读取同步后的GPIO输入 |
| 1 | 0x80000004 | 读写GPIO输出 |
| 2 | 0x80000008 | UART发送忙标志 |
| 3 | 0x8000000c | 写一个待发送字符，忙时忽略 |
| 4 | 0x80000010 | 读Timer当前值，写入启动一次倒计数 |
| 5 | 0x80000014 | 读pending；写bit0=1清pending |
| 6 | 0x80000018 | 完成/错误码 |
| 7 | 0x8000001c | 阶段号，帮助定位卡在哪里 |

REG宏与peripheral.v里的case(offset)必须一致。前面教程的csr.h访问函数由LiteX生成；这里的宏是本章自行定义的接口。

## 1. linker.ld和startup.S如何接起来？

ROM起点0，启动代码输入节.text.init放在最前；普通函数和只读数据接在后面。main RAM起点0x40000000，容量来自GCC参数MAIN_RAM_LENGTH，和SoC构造用同一个值。

```ld
__data_start = .;
```

记录链接器当前运行地址，不创建C变量。收集完.data后再记录__data_end；LOADADDR(.data)取得ROM加载副本的地址。startup.S分别装入源地址、目标地址、结束边界，lw读ROM、sw写RAM，每次前进4字节。

.bss没有ROM初值字节，启动代码在起点到结束边界逐字写0。`__stack_top=ORIGIN(ram)+LENGTH(ram)`算出RAM末尾下一地址；`la sp,__stack_top`只设置SP，随后函数先减SP再写栈。

脚本另要求数据后至少剩512字节栈余量，因为中断入口会额外分配128字节。512是本章候选预留，不是运行时上限，更不构成最坏栈深证明。减小RAM必须同时重链接和重跑。

## 2. main先检查启动是否做对

```c
if(initialized_data!=0x11223344 || zero_initialized || scratch[0] || irq_count)
    fail(0xe1);
```

第一项检查.data复制；后三项检查.bss清零。尚未跑主程序的写入，就先验证启动条件。四态门级仿真中，RAM未初始化的X若进入这些路径，外部结果检查也会失败或超时，不靠预填零掩盖问题。

接着：

```c
for(unsigned i=0;i<32;i++) scratch[i]=0x5a5a0000u+i;
for(unsigned i=0;i<32;i++) if(scratch[i] != 0x5a5a0000u+i) fail(0xe2);
```

先对整个32字缓冲区写不同值，再逐字读回。这里没有覆盖整个main RAM：栈也在同一块RAM高端，不能在正在运行时随便把全RAM覆盖掉。20A用独立的小RAM测试平台做破坏性March实验。

```c
bytes[0]=0x11; bytes[1]=0x22; bytes[2]=0x33; bytes[3]=0x44;
```

四次8位写检查Wishbone sel确实能单独修改对应字节。小端下，最终32位字应为0x44332211。不是把这四个字节按视觉顺序拼成0x11223344。

SRAM的0x10000000和0x100000fc分别是256字节区域的首字与末字起点。容量若变化，这个末地址测试必须更新；main RAM末端则留给实际栈使用，需另外设计不破坏活动帧的边界测试。

## 3. GPIO和UART怎样形成独立证据？

TB把gpio_in设为5；固件读取它，然后将gpio_out写9并读回。TB还从端口检查输出9，因此不是只读同一软件变量来证明GPIO通过。

```c
REG(3)='O'; while(REG(2)){}
REG(3)='K'; while(REG(2)){}
```

发一个字符后等待忙标志清零，再发下一个。TB另用uart_tx下降沿找起始位，在位中心采8位，检查停止位和字符内容；它没有直接读发送器内部shift寄存器。

## 4. Timer IRQ要做哪几件事？

```c
__asm__ volatile("csrw mtvec, %0" :: "r"(trap_entry));
```

将trap_entry地址写到mtvec，告诉CPU发生机器陷入时去哪里执行。

```c
__asm__ volatile("csrw 0xbc0, %0" :: "r"(1));
```

设置当前VexRiscv实现的外部中断源掩码，选bit0。0xbc0是该CPU实现的自定义CSR，不是所有RISC-V CPU都保证存在的标准寄存器。

```c
__asm__ volatile("csrs mie, %0" :: "r"(1u<<11));
__asm__ volatile("csrs mstatus, %0" :: "r"(8));
```

第一句允许机器外部中断，第二句打开机器全局中断使能。外设pending、源掩码、CPU类别使能和全局使能共同决定能否进入中断。

```c
REG(4)=32;
```

给Timer装载32，开始倒计数。计到零后外设保持pending=1，并请求CPU；它不是只高一瞬间的脉冲。

## 5. 中断入口为什么保存这么多寄存器？

普通C调用时，调用者知道哪些寄存器可能被改。但中断可以打断任意指令附近的程序，原程序没有机会先保存自己的临时值。因此startup.S的trap_entry先分配128字节，再保存除x0和sp外的30个整数寄存器。

```asm
addi sp, sp, -128
sw ra, 0(sp)
...
sw t6, 116(sp)
call timer_isr
```

128保证帧保持16字节对齐；30×4=120字节用于保存寄存器，余下8字节是对齐余量。sp本身通过分配前后的相反加减恢复，不需要在该帧再保存一份。

timer_isr检查mcause是0x8000000b，表示机器外部中断；再确认外设pending有效。然后：

```c
REG(5)=1;
irq_count++;
```

先清外设源，再记一次服务。若只增加irq_count却不清pending，mret后可能立刻再次进入中断。程序稍等后要求irq_count恰为1且pending为0，检查清除是否生效。

```asm
lw ra, 0(sp)
...
lw t6, 116(sp)
addi sp, sp, 128
mret
```

恢复整数寄存器和SP，mret使用CPU保存的mepc恢复被打断的执行位置及中断状态。它不同于普通ret：普通ret通常跳到RA，中断返回使用专用陷入状态。当前不支持中断嵌套；若增加嵌套，还必须保存mepc/mstatus等状态并重新预算栈。

## 6. 错误码与观察阶段

| 错误码 | 意思 |
| --- | --- |
| e1 | .data/.bss初始化错误 |
| e2 | RAM缓冲区读回错误 |
| e3 | 字节写或栈函数错误 |
| e4 | SRAM首末字错误 |
| e5 | GPIO输入或输出读回错误 |
| e6 | 等待IRQ超时 |
| e7 | IRQ次数错误或pending没清掉 |
| e8 | 陷入原因或中断源不符合预期 |
| 5a | 所有固件检查到达成功位置 |

阶段1初始化、2存储、3 GPIO、4 UART、5 Timer、6完成。这些编号是教学诊断约定，20章会用它们选定故障/复位注入时间。
