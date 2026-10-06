# 02 —— Wishbone 请求、应答与故障捕获

本章暂时拿掉 CPU，由 Migen 仿真中的测试主设备向一个 32 位寄存器从设备发请求。寄存器位于字节地址 `0x1000`，也就是 Wishbone 字地址 `0x400`。没有 CPU 后，我们可以控制请求并故意制造不正确的应答时序。

```text
测试主设备 ── cyc/stb、adr、we、sel、dat_w ──> 寄存器从设备
           <────────── ack、err、dat_r ───────
```

## 这里用到哪些 LiteX / Migen 接口？

本章不创建 `SoCCore`，而是直接用 LiteX 的 `wishbone.Interface` 描述从设备接口，再用 Migen 的 `Module`、`Signal`、`comb` 和 `sync` 写寄存器行为。`verify.py` 里的 Python generator 是测试主设备，逐拍驱动同一组总线信号；`run_simulation` 执行主设备和从设备。这样先把 Wishbone 应答规则单独测清楚，再把同类接口接进完整 SoC。

`RegisterSlave` 把 `data_width=32`、`address_width=32` 和 `addressing="word"` 配在一起：数据一次 32 位，`adr` 的单位是字而非字节，所以本章字节地址 `0x1000` 对应 `adr=0x400`。`sel` 有 4 位，逐位控制 4 个字节。若将 `addressing` 改成 `"byte"` 却不改测试地址，访问就会跑到完全不同的位置；若把数据宽度改成 64 位，byte select 和数据掩码也必须一起扩展。

## `wishbone.Interface` 怎样变成 RTL？

`wishbone.Interface(...)` 创建一组 Migen 信号。它是连接器，不是完整的总线实现：主设备和从设备使用匹配的信号线，从设备具体做什么由模块里的赋值决定。

```python
self.bus = bus = wishbone.Interface(
    data_width=32, address_width=32, addressing="word")
self.comb += [bus.dat_r.eq(self.value), bus.err.eq(0)]
self.sync += If(state == RESP, ...)
```

组合赋值会变成连续 RTL 连接，例如 `assign dat_r = value; assign err = 0;`。同步语句会变成 `always @(posedge sys_clk)` 中的寄存器和下一状态逻辑。导出的 Verilog 在 [`results/02/rtl/02-normal.v`](../../results/02/rtl/02-normal.v)，可以查看其中 `ack`、`dat_r` 和 `always` 逻辑。`verify.py` 中的 Python generator 是测试主设备，不会变成 RTL；它在 Migen 仿真中驱动硬件从设备。

本章没有 `SoC.bus.add_slave`，因为这里没有 SoC 地址译码器。测试主设备直接驱动从设备接口。`RegisterSlave` 自己比较输入字地址和 `WORD_ADDRESS`；地址不匹配时状态机不会离开 `IDLE`，所以不会产生 ACK。01/03 章的 LiteX `add_slave(..., region=SoCRegion(...))` 则是在 SoC 总线上先选择从设备，再把请求送进去。

`wait_cycles` 控制状态机在 `WAIT` 状态停留多久；它只改变应答延迟，不改变地址。`fault` 则故意让 ACK 提前出现、保持过久或永不出现。特别是 `no_ack` 下主设备仍保持 `cyc/stb`，只能由测试设置的等待上限退出，否则软件测试会无限等下去。

`wait_cycles=2`、负例中的 `max_wait=6`、寄存器地址 `0x1000` 和 `0xaabbccdd` 等数据都是本实验的测试参数。六拍是检查器的超时上限，不是 Wishbone 规定的应答期限；改它只会改变检查器何时判超时，不会改变协议。字节地址到字地址的换算则依赖当前 32 位、按字寻址的接口；若改总线宽度或寻址方式，测试地址和 byte-lane 检查也要一起调整。

## 读一笔事务

主设备拉高 `cyc` 和 `stb`，给出地址和操作，并在完成前保持请求字段稳定。`we=0` 是读，`we=1` 是写。读操作在 `ack` 完成事务时取用 `dat_r`。`sel` 选择数据字节通道；`sel=0001` 只改 32 位字的最低字节。

```text
              请求         等待         应答          空闲
cyc/stb        1/1          1/1          1/1           0/0
ack              0            0            1             0
```

寄存器初值是 `0x11223344`。即使 `ack=0` 时 `dat_r` 已经显示这个值，也不能算读操作完成；主设备只在应答周期接受这个读值。

## 常见问题

### 每个信号在这里表示什么？

| 信号 | 本实验里的含义 |
| --- | --- |
| `cyc`、`stb` | 一笔事务正在进行，当前请求有效 |
| `adr` | Wishbone 字地址；`0x400` 对应字节地址 `0x1000` |
| `we` | `0` 读，`1` 写 |
| `dat_w`、`dat_r` | 发给从设备的写数据、从从设备返回的读数据 |
| `sel` | 32 位数据的四个字节使能 |
| `ack` | 从设备确认本次请求已完成 |
| `err` | 错误应答；本实验预期它保持为低 |

### 我们怎么捕获到失效，而不只是看到仿真失败？

测试在特定时刻检查协议条件，并把每拍采样写入 CSV 和 VCD。发请求前要求 ACK 为低；请求过程中逐拍等 ACK，超过上限就超时；收到 ACK 后撤销 `cyc/stb`，再检查 ACK 是否回低。这样能区分错误发生在请求之前、事务等待期间，还是完成之后。

| 注入的场景 | 检查器采样什么 | 如何判定失效 |
| --- | --- | --- |
| `no_ack` | 正确地址 `0x400`，请求保持有效，逐拍检查 ACK | `max_wait=6` 被超过；检查器先加计数再比较，因此计到 7 拍时报告超时 |
| `unmapped` | 请求地址改为 `0x401`，超出该从设备的一字地址范围 | 波形给出未命中地址且没有 ACK；因此超时与未映射有关 |
| `early_ack` | 主设备发请求前的 ACK | 空闲总线上的 ACK 被请求前检查立即判为协议错误 |
| `held_ack` | 主设备撤销 `cyc/stb` 后的 ACK | 应答后空闲总线上 ACK 仍为高，被收尾检查判错 |
| `wait2` | 正常请求的 ACK 时刻 | CSV 中 ACK 前多出两个等待周期 |

事务检查器负责判定通过或失败；逐周期记录器保存能解释结果的证据。只有一个超时信息无法区分“地址没有从设备”和“从设备看到了请求却没有回答”；CSV/VCD 中的地址和握手信号可以把两者区分开。

这个超时数是检查器自己的设置：`max_wait=6` 表示允许计数 6 拍，在计数变成 7 时才判失败；它不是总线时序规则。未映射地址也用相同上限，保证两种无应答波形都能确定结束。

### 为什么 ACK 必须对应当前有效请求？

主设备把 ACK 理解为“这笔事务已经完成”。空闲时出现 ACK，可能被误认为下一笔事务的回答；完成后 ACK 一直保持，也可能让一笔访问看起来完成多次。要求 ACK 只在有效请求期间出现一个周期，可以避免陈旧或重复应答。

### 字节通道实验检查什么？

测试先写入 `0xaabbccdd`，再逐个写入字节通道并读回。每个 `sel` 位对应一个字节。最后测试 `sel=0`，寄存器应保持不变。这些步骤能抓到忽略 byte enable 或写错字节的从设备。

## 运行与观察

```sh
python3 chapters/02-wishbone/verify.py
python3 chapters/02-wishbone/verify.py --case wait2
```

默认运行覆盖正常读写和读回、字节使能、零选择、等待两拍、无 ACK、提前 ACK、ACK 悬挂和未映射地址。输出写到 `results/02/<case>.csv` 和 `.vcd`。先看 `normal.csv`：找到 `cyc=stb=1`，沿着同一地址找到 `ack=1`，然后确认请求与 ACK 都回到低。CSV 不需要波形查看器也能读；VCD 可用 GTKWave 查看。

每次运行还会按构造参数把从设备 RTL 导出到 `results/02/rtl/02-<case>.v`。`unmapped` 只改变 Python 测试主设备的地址，因此使用正常从设备 RTL。对比 `02-normal.v`、`02-wait2.v` 和 `02-no_ack.v`，可以看到 Python 参数或故障分支怎样改变生成的状态机。

## PASS 能证明什么？

正常案例通过表示寄存器从设备在本实验覆盖的时序和字节使能规则下正确返回、保存数据。负例通过表示对应的协议错误被抓到。本章只有单主设备、单从设备的 Classic 单次事务，不代表已经实现 burst、多主设备或仲裁。
