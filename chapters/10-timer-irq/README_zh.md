# 10 —— 定时器事件与 CPU 中断

本章把容易混在一起的三件事分开看：定时器归零、LiteX 拉高中断输入、CPU 接受机器态外部中断。固件分别测试轮询、单次中断、周期中断，以及定时器运行中复位。

```text
ProjectTimer 归零
  → EventManager 在事件使能时置 pending
  → LiteX IRQ handler 把 timer0 接到 VexRiscv externalInterruptArray[0]
  → 固件设置 VexRiscv 的源掩码 CSR `0xbc0` bit 0
  → mie.MEIE 和 mstatus.MIE 允许 CPU 进入 trap
  → mtvec 跳到 trap_entry → isr 清 timer pending → mret 返回固件
```

这个 SoC **没有 PLIC**。LiteX IRQ handler 把中断源直接连接到 VexRiscv 中断向量。中断源编号由 LiteX 根据本次 SoC 分配，并记录在生成地图里；当前配置中 `timer0` 是输入 0。

## SoC 配置了什么？

`SoCCore` 提供 4 KiB ROM、4 KiB 集成 SRAM 和 16 KiB `main_ram`。栈和 C 数据放在 `main_ram`。这里关闭 SoCCore 自带的 `with_timer`，因为我们实例化了 CSR 名称明确的 `ProjectTimer`。`add_module()` 把它加入硬件层次；`self.irq.add("timer0")` 把它的 EventManager IRQ 接到 CPU 中断向量。

测试中的轮询 `load=600`、单次 `load=300` 和周期 `reload=1200` 是为了让仿真中的变化容易观察，并非 Timer 固定值。等待上限和预期 ISR 次数也只是测试参数。

## 为什么 ISR 不需要 claim PLIC？

有 PLIC 的系统会通过 claim/complete 寄存器仲裁中断源；本章 LiteX VexRiscv SoC 没有 PLIC。CPU 把 LiteX IRQ 线作为机器态外部中断处理。当前 VexRiscv RTL 还有一个逐源掩码 CSR `0xbc0`：必须设置 bit 0，`externalInterruptArray[0]` 才会进入 `mip.MEIP`。固件还要打开 `mie.MEIE`（bit 11）和全局 `mstatus.MIE`。三层都允许后 CPU 才接受中断。ISR 在 `mret` 前清除 Timer 自己的 `ev_pending`。若 pending 没清，IRQ 线会保持高电平，CPU 返回后可能立刻再次进入 trap。

CPU 把被打断的 PC 保存到 `mepc` 并更新机器态 trap 状态。`trap_entry` 把 C 处理函数可能改写的通用寄存器保存到 RAM 栈，调用 `isr` 后再恢复，最后执行 `mret`。因此启动代码必须先把 `sp` 设到有效 RAM，再允许中断。

## 测试观察什么？

轮询阶段关闭中断，观察计数递减；单次模式要求恰好进入一次 ISR；周期模式要求再进入三次，每次 ISR 都清除事件，使定时器能再次产生中断边沿。日志记录 IRQ 上升/下降、ISR 次数和最终完成写入。复位负例分别在计数过程中和 ISR 开始时触发复位，然后要求固件重新完成检查。

`run.py` 会先检查生成的 memory/CSR map，再编译固件。第一次实验曾观察到 IRQ 线已经拉高、CPU 却没进入 ISR；补上 VexRiscv 专用的 `0xbc0` 源掩码后，才和标准 RISC-V 中断位一起完成路径；它还核对 `timer0_interrupt` 分配，并把结果写入 `results/10/irq_map.csv`。当前 CPU 输入编号为 0，这是本次 SoC 的分配结果，不是 LiteX 永远固定的编号。

```sh
PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py
```

PASS 证明仿真中的 Timer 事件送到 CPU、ISR 清除事件并返回固件。它不证明开发板上的中断接线或实体定时器精度。
