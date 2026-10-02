# 第 09 章：让 CPU 真正经过 UART 引脚收发

上一章的 GPIO 一次读写就能看到电平。串口（UART）不同：一个字节要沿一根线按时间送出。本章让 CPU 先发送 `U`，再发送 `HELLO`，最后连续发送 `123456`，并把 TX 接回 RX。CPU 收到末字节 `6` 后再发一次，形成真正的回显。仿真器从 **TX 引脚波形**解码字节，CPU 从 UART 接收 FIFO 读回字节；两边都必须得到 `UHELLO1234566`。

## 输入与概念

本章文件都在本目录：`soc.py` 定义 LiteX SoC 和引脚模型；`main.c` 是 CPU 程序；`startup.S` 设置栈并初始化 C 数据；`linker.ld` 指定 ROM 和 RAM；`run.py` 生成 CSR 头文件、编译固件、构建并运行 SoC。还需第 00 章的 LiteX、RISC-V 工具链和 Verilator。

| 名词 | 这里的意思 | 看哪里 |
| --- | --- | --- |
| TX / RX | 发送输出脚 / 接收输入脚 | `serial.tx` / `serial.rx` 波形 |
| 8N1 | 1 个低电平起始位、8 个数据位、无校验、1 个高电平停止位 | `SerialLoopback` 按位采样 |
| 波特率 | 每秒发送的位数 | `BAUD=100000`，系统时钟 `1000000` Hz，每位约 10 个时钟 |
| FIFO | 硬件里排队的字节缓冲区 | `uart_txfull_read()` / `uart_rxempty_read()` |
| CSR | CPU 用 load/store 访问 UART 的控制和数据寄存器 | `csr.csv`、`generated/csr.h` |
| 回环 | 把 TX 引脚连接到 RX 引脚 | `pads.rx.eq(pads.tx)` |

```text
CPU store → Wishbone → CSR bridge → UART 发送 FIFO → TX 引脚
                                                   │ 8N1 电平
                                                   └──────────→ RX 引脚 → UART 接收 FIFO
CPU load  ← Wishbone ← CSR bridge ←──────────────────────────────────────┘
```

TX 空闲为高电平，拉低表示一帧开始；后面从低位到高位送出 8 个数据位，最后回到高电平。`SerialLoopback` 只接线和采样引脚，不直接读取 CPU 要发送的字节。因此 `UART_TX_BYTE` 是**引脚解码结果**；`UART_RX_BYTE` 是 CPU 从接收 FIFO 读出后写给测试端点的值。两者相同才说明整条路径走通。

## 参数和地址

本章保持 1 MHz 系统时钟，设置 100000 bit/s，方便每位约用 10 个时钟观察。UART TX/RX FIFO 各为 4 字节。`SoCCore` 添加真实 LiteX UART；`with_uart=False` 仅关闭默认实例，随后 `add_uart(..., baudrate=BAUD, fifo_depth=4, rx_fifo_rx_we=True)` 显式创建本章 UART。`rx_fifo_rx_we=True` 表示 CPU 读取 `rxtx` 时弹出一个接收字节。UART 有 IRQ 线并分配为 IRQ 1（IRQ 0 在 VexiiRiscv 中保留），但本章 `ev_enable` 复位为 0，程序只轮询；下一章用 Timer 学习中断。

程序通过本章 Builder 生成的 `csr.h` 调用 `uart_txfull_read()`、`uart_rxtx_write()`、`uart_rxempty_read()`、`uart_rxtx_read()`。`run.py` 在编译前核对 `csr.csv`：UART 数据寄存器 `uart_rxtx` 为 `0xf0000800`，`txfull` 为 `0xf0000804`，`rxempty` 为 `0xf0000808`。ROM、SRAM、main RAM、完成端点、CSR 空间的位置也逐项检查。生成头文件和最终运行的 SoC 使用同一组参数。

`main.c` 发送单字符和短字符串时，每发一字节就等接收并比较。发送 `123456` 时先连续写入 4 字节 FIFO，观察一次 `txfull=1`，再依序取出所有接收字节。最后把**刚收到的** `6` 再写入 UART，并检查回环读回。`txfull=1` 只说明发送 FIFO 暂时不能再收字节，线路仍可能正在发送；`rxempty=1` 则表示 CPU 现在无字节可读。两个等待循环都有限次，卡住会写失败码。

## 运行与读日志

```sh
python3 chapters/09-uart/run.py
```

正常运行会看到以下相邻的 TX/RX 行（`0x55` 是字符 `U`）：

```text
UART_TX_BYTE value=0x55
UART_RX_BYTE value=0x55
UART_TX_BYTE value=0x48
UART_RX_BYTE value=0x48
...
UART_FIFO_FULL seen=0x00000001
...
SOC_COMPLETE data=0x0000005a
```

验收脚本逐字节比较引脚解码和 CPU 读回值，检查发送顺序、FIFO 满状态和成功码。它还把**外部监视器**的采样间隔故意从 10 改成 12 个时钟；UART 和 CPU 仍按正确速度工作，但监视器解码错误，产生 `EXPECTED_FAIL 09-WRONG-BAUD`。例如正确首字节 `0x55` 会被误读成 `0xa9`。这说明终端波特率错误时，即使软件内部成功，外部观察也不可信。

第三次仿真在 TX 起始位下降沿后注入一次系统复位：发送尚未完成时，`UART_RESET_ASSERT` 出现；释放后 CPU 从 ROM 重启，重新发送并回读完整的 `UHELLO1234566`。复位脉冲由不随系统复位清零的仿真计数器产生，避免反复复位。记录在 `results/09-reset-tx/run.log`。

主要证据在 `results/09/run.log`、`results/09-wrong-baud/run.log`、`results/09/wrong-baud.log`、`results/09-reset-tx/run.log`、`results/09/builder/csr.csv` 和 `results/09/builder/gateware/sim.vcd`。在波形中沿 TX 下降沿开始，以 10 个 `sys_clk` 为一位，数起始位、8 个数据位和停止位；对照日志的 `UART_TX_BYTE`。`results/09/firmware/program.map` 用来检查程序及栈所在区域。三次仿真都在超时内结束；错误波特率实验必须由检查器拒绝。

## 常见问题

### `UART_TX_BYTE` 和 `UART_RX_BYTE` 分别证明什么？

前者由独立监视器从 TX 引脚逐位采样解码，证明线上真的出现了串行帧；后者由 CPU 从 RX FIFO 读出，再写入仿真探针，证明接收链路和软件读回。若测试直接把待发送字节抄进日志，就不能证明 TX 引脚和 UART 接收器工作。本章要求两边逐字节、按顺序相等。

### `txfull=1` 是否表示发送结束？

不是。它只表示发送 FIFO 暂时没有空位。FIFO 中已有的字节可能还在移位寄存器和 TX 引脚上发送。要证明帧结束，应观察停止位/线路空闲或收到回环数据，不能只看 `txfull`。

### 错误波特率负例改了 CPU 的设置吗？

没有。CPU 和 UART 仍以 100000 bit/s 工作；测试故意让外部监视器按每位 12 个时钟采样，而正确值是 10 个。这样错误明确落在“观察者采样设置”上，监视器会把线上正确帧解成错误字节并拒绝结果。

### 复位为什么安排在 TX 起始位之后？

这样能确认发送帧尚未完成时复位确实打断了正在进行的硬件状态。复位释放后，CPU 必须重新从 ROM 启动并完整发送、接收预期字节；只看到复位脉冲不足以证明系统恢复。

## 本章速记

1. UART 写 CSR 先进入发送 FIFO，随后才成为 TX 引脚上的逐位电平。
2. `txfull` 管发送排队，`rxempty` 管接收可读；寄存器访问完成不等于一帧已经发完。
3. 回环读回证明 RX 路径，引脚解码证明 TX 波形；两份证据要一致。
4. 波特率要和时钟匹配。终端用错采样速度会读出错误字节。
