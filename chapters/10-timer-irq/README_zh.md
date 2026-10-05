# 第 10 章：从轮询计时到 CPU 真正响应中断

上一章的 UART 程序不断查看 `rxempty`，这是**轮询**：CPU 主动问外设。本章先用同样方法读取定时器，再让定时器主动通知 CPU。实验依次做计数递减、一次性中断、周期中断；最后停表并确认没有额外 ISR。

## 输入与概念

`soc.py` 定义单核 SoC、定时器及 IRQ 观察点；`main.c` 执行三段实验；`startup.S` 设置栈、陷阱入口和 C 初始化；`linker.ld` 放置 ROM/RAM；`run.py` 生成 CSR 头文件、交叉编译并仿真。除本章文件外，只需第 00 章工具链和 LiteX 环境。

| 名词 | 好懂的意思 | 本章证据 |
| --- | --- | --- |
| 倒计数器 | 每个时钟减 1，减到 0 产生事件 | `TIMER_POLL` 前后两个值 |
| `load` / `reload` | 启动时装入的数 / 到零后重新装入的数 | 单次设 `reload=0`，周期设 `reload=1200` |
| `update_value` / `value` | CPU 先要求锁存当前计数，再读锁存值 | `timer0_update_value_write` 后读 `timer0_value_read` |
| pending / enable | 事件已发生的记录 / 是否让事件拉高 IRQ 线 | `timer0_ev_pending` / `timer0_ev_enable` |
| IRQ | 外设给 CPU 的中断请求线 | `IRQ_LINE_ASSERT/CLEAR` 和 VCD |
| ISR | CPU 暂停主程序后运行的中断处理函数 | `TIMER_ISR` 日志；返回后主程序写完成码 |
| `mtvec` / `mret` | 软件写入的中断入口地址 / 从中断返回的指令 | `startup.S` 的 `trap_entry` |

```text
timer0 count 到 0
  → ev.pending 置 1
  → ev.enable=1，timer0 IRQ 线拉高
  → PLIC 源 1 使能、优先级为 1，且 mie.MEIE 和 mstatus.MIE=1
  → CPU 跳到 mtvec=trap_entry
  → 保存现场 → 调 isr() → 清 pending → 恢复现场 → mret
  → CPU 回到被打断的主程序
```

## LiteX 的哪些配置把定时器接到 CPU？

SoC 使用 1 MHz 时钟、复位地址 0、4 KiB ROM、4 KiB 片上 SRAM 和 16 KiB main RAM。main RAM 放 C 数据、栈和陷阱处理程序保存的寄存器。这里关闭 `with_timer`，因为本章改为实例化 CSR 名称明确的 `ProjectTimer`。`add_module("timer0", ...)` 把 CSR/事件逻辑加入设计，`self.irq.add("timer0", use_loc_if_exists=True)` 则通过 LiteX IRQ 结构连接事件；本次生成地图中它是 PLIC source 1。

`load` 和 `reload` 的单位是 `sys` 时钟周期，不是微秒：1 MHz 时 1200 次计数约为 1.2 ms。改 `clk_freq` 会改变实际经过时间，但不会改变计数值；把 `reload` 从 0 改成正数，则从单次事件变成周期事件。测试预期和固件配置必须同时跟着调整。

测试里的轮询 `load=600`、单次中断 `load=300` 和周期 `reload=1200` 都是为了让事件在短仿真里清楚可见而选择的参数，不是定时器架构规定的常数。改它们时，要一起检查轮询范围、事件等待上限和周期 ISR 次数。固件还选择 PLIC priority `1`、threshold `0`；这个单中断实验中，任何高于 threshold 的正优先级都可用。PLIC source 1 是本次构建的分配；增加其他中断源后它可能变化。

这里有**四道条件**：定时器事件的 `ev_enable`、PLIC 中源 1 的使能/优先级与 CPU 的 mie.MEIE，以及全局 `mstatus.MIE`。它们都允许后，pending 才能让 CPU 进 ISR。进入陷阱时 CPU 保存返回 PC 到机器态 CSR；本章 `trap_entry` 再把会被 C 函数改写的通用寄存器存入栈，返回前恢复，最后执行 `mret`。`sp` 所指的内存位于 main RAM，因此嵌套调用与中断都需要足够栈空间。

## 定时器怎么接进 LiteX

本机 LiteX `Timer()` 在当前 Python 组合上不能自动提取 CSR 名称，构造时会报 `Cannot extract CSR name from code`。本章 `ProjectTimer` 把 LiteX Timer 的五个寄存器、倒计数逻辑和 `EventManager` 事件连接逐项写出，并给 CSR 明确命名。它仍使用 LiteX 的 `CSRStorage`、`CSRStatus`、`EventSourceProcess` 和 SoC IRQ 路由；不是在 Python 里假装触发 ISR。这个实现让学生能直接看见“计数到零 → pending → IRQ”的连线。

定时器 CSR 在 `0xf0000800` 起：`load`、`reload`、`en`、`update_value`、`value`、`ev_status`、`ev_pending`、`ev_enable`，每项相隔 4 字节。`csr.csv` 中 `timer0_interrupt,1` 表明它接 VexiiRiscv PLIC 的源 1。`run.py` 编译前和 Builder 完成后都核对这些地址；C 程序使用**本章生成的** `generated/csr.h`。

## 三段程序逐步看

1. **轮询：** 关事件使能，写 `load=600`、`reload=0`，启动计数；两次写 `update_value` 后读 `value`。CPU 记录的这次运行是 `0x24e=590` 下降到 `0x0fe=254`，故 `TIMER_POLL packed=0x00fe024e`。这里低 16 位是第一次读数，高 16 位是第二次。精确数值随编译和总线等待可变，必须满足 `0 < 第二次 < 第一次 ≤ 600`。
2. **一次性中断：** 写 `load=300`、`reload=0`，清旧 pending，打开事件和 CPU 中断。计数到零后 IRQ 拉高，ISR 写 1 清 pending，并记录 `phase=1,count=1`。等待一段时间后仍必须是 1 次。`reload=0` 使计数保持在 0，不再产生新的上升沿。
3. **周期中断：** 写 `load=0`、`reload=1200`，重新启用计数。每次到 0 后装回 1200。ISR 再进入 3 次，累计计数 2、3、4。主程序停表、关事件和 CPU 中断，再等待，计数必须保持 4。

ISR **先从 PLIC claim 领取源 1，清 Timer pending，再向 PLIC 写回 claim 完成号**。如果只从 ISR 返回而不清，IRQ 线仍高，CPU 可能马上重新进入；这也是典型的“中断风暴”。`inside_isr` 检查重入，所有等待有上限，失败时向完成端点写 `0xe1`–`0xe5`，不会伪报 PASS。

运行器另做两次单次复位。`10-reset-count` 在轮询阶段计数器运行时复位；`10-reset-isr` 在首次 ISR 写出观察值时复位。复位计数器位于不随 `sys` 复位清零的 `por` 时钟域，所以每次只注入一次。释放后 CPU 都必须从 ROM 重启，并重新完成 1 次轮询、4 次中断及最终完成写。可在各自的 `run.log` 中看到 `TIMER_RESET_ASSERT/RELEASE`；ISR 复位实验里，第一次 `TIMER_ISR packed=0x00010001` 出现在复位前，重启后的 4 次记录从 1 重新计数。

## 运行与证据

```sh
python3 chapters/10-timer-irq/run.py
```

日志关键段：

```text
TIMER_POLL packed=0x01060256
IRQ_LINE_ASSERT source=timer0
IRQ_LINE_CLEAR source=timer0
TIMER_ISR packed=0x00010001
...
TIMER_ISR packed=0x00020004
SOC_COMPLETE data=0x0000005a
```

`TIMER_ISR` 的高 16 位是阶段号、低 16 位是 ISR 累计次数。脚本要求 4 次 ISR 依次为 `(1,1)`、`(2,2)`、`(2,3)`、`(2,4)`，并且 IRQ 线恰好拉高、清除各 4 次。只有 CSR 表说明“接了定时器”；只有硬件 IRQ 线变化说明“提出请求”；ISR 计数加上主程序完成码才说明 CPU 真正接收、清除并返回。

查看 `results/10/builder/csr.csv`、`irq_map.csv`、`run.log`、`builder/gateware/sim.vcd` 和 `firmware/program.map`。VCD 中先找 `timer0` 的计数、pending、IRQ，再找 CPU 的 `externalInterruptArray[0]`，核对先拉高后执行 ISR。若没有 ISR，按事件使能、CPU IRQ 掩码、全局中断使能、`mtvec` 顺序排查。

## 常见问题

### 定时器到零后，CPU 为什么不一定进入 ISR？

计数到零只产生外设事件。还必须让 Timer 事件使能、PLIC 对应源使能、CPU 的机器外部中断掩码和全局中断位都打开，并且 `mtvec` 指向有效入口。缺一道，IRQ 可能不连到 CPU，或 CPU 不接受它。检查时按这条路径从 Timer pending 一直跟到 CPU 中断输入。

### 为什么 ISR 要同时处理 Timer pending 和 PLIC claim/complete？

Timer pending 表示外设事件仍在；PLIC claim 让 CPU 取得当前中断源，complete 则告诉 PLIC 处理结束。只执行 `mret` 而不清外设 pending，IRQ 仍会保持有效，CPU 返回后可能立刻再次进 ISR。本章记录 IRQ 上升/下降次数，并核对 ISR 次数和最终完成码。

### 本章为什么自己写 `ProjectTimer`，不直接用 `Timer()`？

在本项目固定的 Python/LiteX 组合下，LiteX `Timer()` 的 CSR 名称自动追踪报 `Cannot extract CSR name from code`。本章给寄存器显式命名，保留 LiteX 的 CSR、EventManager 和 SoC IRQ 路由，同时把计数到 pending 再到 IRQ 的逻辑写清楚。它不是由 Python 直接调用 ISR。

### `TIMER_POLL` 数字每次运行都一样吗？

不要求完全相同。CPU 读计数器的时刻受指令和总线等待影响，因此本章检查第二个值小于第一个且两者都在装载值范围内。中断阶段则检查确切事件数、阶段号和 IRQ 边沿数。

## 本章速记

1. 轮询是 CPU 主动读；中断是外设事件经允许后通知 CPU。
2. `pending` 是事件记录，`enable` 是连到 IRQ 线的开关；ISR 清 pending 后再返回。
3. 单次计时 `reload=0`，周期计时 `reload>0`；两者都从 `load` 启动。
4. IRQ 波形、ISR 次数和主程序完成码各证明不同环节。
