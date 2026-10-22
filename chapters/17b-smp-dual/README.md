# 17B：两个 hart 怎样合作，而不是只把数量改为 2？

本章让真实 VexRiscv-SMP 双核 RTL 执行同一份 C 固件。每个 hart 留下独立结果，还一起更新一个共享计数器。**当前通过的是 RTL 仿真，双核 FPGA 上板仍未执行。**

## 1. 两个核与共享内存的关系

```text
hart0：PC、寄存器、私有栈、L1 缓存 ─┐
                                   ├─ SMP 一致性互连 ─┬─ 外设 Wishbone → ROM/UART/CLINT/PLIC
hart1：PC、寄存器、私有栈、L1 缓存 ─┘                  └─ 原生内存接口 → 共享 RAM 模型
```

两个 hart 的编号分别为 0、1，通过 `mhartid` 读取。两者取同一份 ROM 指令，但有不同的执行状态。

当前选用已有的双核 RTL：每 hart 的指令/数据缓存各 8 KiB、2 路；缓存接口 64 位，原生内存接口 128 位。它们都是选定配置，不是双核必须使用的数值。这个组合同时暴露 coherent DMA 接口，本章没有接入 DMA 主设备。

本章 RAM 是接在原生内存接口上的 **64 KiB 行为模型**，不是实际 DDR，也没有 DDR PHY。命令、写数据、读数据分别握手；每个命令访问一个 128 位字，并支持字节写掩码。两个原生接口访问同一个存储数组；模型只接受该数组范围内的地址。

## 2. 为什么要分开栈与邮箱？

```text
0x40000040              共享原子计数器
0x400000c0、0xc4        两个 hart 的软件中断计数
0x400000d0、0xd4        两个 hart 的定时器中断计数
0x40000100              hart0 邮箱
0x40000140              hart1 邮箱
0x40002000              hart0 RAM 测试区
0x40003000              hart1 RAM 测试区
...
0x40010000              hart0 初始 sp
0x4000f800              hart1 初始 sp
```

地址均是本实验的字节地址。每个栈预留 2048 字节：`sp = __stack_top - (hartid << 11)`。两核用同一个栈，会互相覆盖函数保存的返回地址和数据。

邮箱间隔 64 字节，与这个核心的缓存行大小对齐，减少两个核频繁修改同一行带来的竞争。每个邮箱保存：结果、迭代数、hart 编号、完成标记。

## 3. 两个核怎样开始、怎样完成？

```text
hart0                                    hart1
清邮箱、IRQ 计数、原子计数器             等待自己的 CLINT msip
fence：保证初始化先于释放动作
写 hart1 的 msip=1 ────────────────────→ 清 msip，开始执行
本核 CLINT 软件/定时器中断检查                  本核 CLINT 软件/定时器中断检查
本核 RAM 模式/字节写检查                 本核 RAM 模式/字节写检查
求和并做 WORK 次原子加法                 求和并做 WORK 次原子加法
写本核结果、fence、完成标记              写本核结果、fence、完成标记
等待两个邮箱完成 ←─────────────────────┘
核对两份结果、原子总数、IRQ 计数
独占 UART，输出汇总
```

中断在释放 hart1 时仍关闭；hart1 先轮询并清除启动用的 `msip`，之后才启用软件中断测试。这样不会把“启动通知”混成“测试中断”。

每次系统复位后重新初始化邮箱，并通过 CLINT 再次释放 hart1。这个流程避免复位后把上一次残留的完成标记误认成新成功。

## 4. `volatile`、`fence`、原子指令分别解决什么？

- `volatile` 要求编译器真正发出内存访问，不能把轮询值一直留在寄存器里。
- `fence rw,rw` 约束前后内存访问的顺序，让结果写入先于完成标记。
- `amoadd.w.aqrl` 把共享计数器的读、加、写作为一个原子操作，避免两个核同时加一时丢失更新。
- 缓存一致性由当前 SMP RTL 实现。`volatile` 和 `fence` 都不能替代一个缺失的一致性机制。

默认每个 hart 加 1000 次，最终必须是 2000。除此之外，主机还要求看到两条不同 hart 的邮箱记录；只有一个总 PASS 字符串不够。

## 5. 正例与失效实验

```bash
# 两核正常执行；默认完整复位运行两次
python chapters/17b-smp-dual/run.py

# 改变工作量、让 hart1 晚一些工作，重复三次启动
python chapters/17b-smp-dual/run.py --work 257 --delay-hart 3000 --reboots 3 \
  --output results/17b-delayed

# hart1 不响应：hart0 必须报告超时
python chapters/17b-smp-dual/run.py --stop-hart \
  --output results/17b-stop-hart

# 完成标记正常，但结果错误：必须报告 mailbox 错误
python chapters/17b-smp-dual/run.py --bad-mailbox \
  --output results/17b-bad-mailbox
```

超时门槛是当前固件的 200000 次轮询，不是固定毫秒数；调整工作量或加入更长延迟时需要重新评估。`--delay-hart` 的单位是延迟循环次数，也不是时钟周期。

故障捕获链：

```text
--stop-hart → hart1 不写完成标记 → hart0 轮询超限 → UART: SMP FAIL timeout
--bad-mailbox → 故意翻转求和结果 → hart0 对照预期 → UART: SMP FAIL mailbox
                                                   ↓
                         主机要求准确故障类型和预期复位次数 → 负例 PASS
```

默认正常日志：

```text
SMP HART 00000000 count=000003E8 sum=0007A314
SMP HART 00000001 count=000003E8 sum=0007A314
SMP ATOMIC count=000007D0
SMP IRQ PASS
SMP TIMER PASS
SMP PASS harts=00000002
```

`results/17b/rtl/` 收齐 CPU 集群、缓存 RAM 模块、SoC 顶层、共享内存模型、初始化文件和测试台。`summary.json`、`run.log` 保存真实验证结果；依赖与 17A 相同，本章逻辑文件独立。

## 6. 目前没有证明什么？

本实验验证了这些有限场景中的共享可见性、原子更新、中断与复位启动。尚未覆盖全部缓存一致性状态、外部 PLIC 中断、错误邮箱地址、随机长时间 SMP 压力，也没有双核资源/时序或上板结论。

上板需要落实这份共享 RAM 如何映射到 FPGA 存储资源，或替换为真实 DDR 通路，再检查资源和时序。当前 64 KiB RAM 加上双核缓存、ROM/SRAM 不保证能装进这块板，需要先做容量与 RAM 推断审计，必要时调整参数；仿真通过不能视为已完成板卡适配。
