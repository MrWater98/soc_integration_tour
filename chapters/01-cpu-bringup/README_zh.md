# 01 —— VexiiRiscv 能取指并写数据吗？

这是第一个 CPU 级实验。使用 LiteX 原生 VexiiRiscv 封装、64 字节初始化 ROM 和一个内存映射写入端点。程序尽量短，方便直接从日志理解发生了什么。

```asm
addi x1, x0, 64   # x1 = 0x40
sw   x1, 0(x1)    # 向字节地址 0x40 写入 0x40
```

## 连接关系

```text
VexiiRiscv pBus（AXI-Lite，字节地址）
                  │
                  ▼ LiteX AXILite2Wishbone 适配器
          Wishbone Classic，32 位
           ├── ROM       0x00000000–0x0000003f
           └── 写入端点  0x00000040–0x0000007f
```

CPU 外设总线是 AXI-Lite，本系统 LiteX 主总线是 Wishbone。LiteX 注册 CPU master 时会插入协议适配器；项目没有自己实现这座桥。

## 常见问题

### 为什么只用两条指令？

`addi` 产生一个确定的数值，`sw` 把它变成总线上可观察的事务。如果端点收到预期地址和数据，就说明 CPU 已退出复位、取到指令、执行了指令并发出了 store。此时不需要 C 运行库、栈或其他外设来增加干扰。

### 第一次 `FETCH` 能证明指令执行了吗？

它证明复位地址处的一次 ROM 读取完成。VexiiRiscv 可能预取指令，因此一条 fetch 日志不能证明某条指令已经执行。端点收到 `0x40` 写入是更强的证据：只有程序执行到 `sw` 才会发出这个写操作。

### 为什么 `0x40` 会变成 Wishbone 地址 `0x10`？

固件和 LiteX 地址图使用字节地址。这里的 32 位 Wishbone 端点按字寻址，每个地址单位代表 4 字节，所以字节地址 `0x40` 对应 Wishbone 字地址 `0x40 / 4 = 0x10`。转换的是地址单位，写入的数据仍然是 `0x40`。

### Python 文件里为什么找不到 `AXILite2Wishbone`？

本章选择 VexiiRiscv 和 LiteX 的 Wishbone 主总线。LiteX 注册 CPU master 时会检查总线类型，并添加内置 `AXILite2Wishbone` 适配器。构建日志会出现 `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit`。实现位于 LiteX 的 `litex/soc/interconnect/axi/axi_lite_to_wishbone.py`；本项目无需直接调用它。

### no-ACK 实验具体捕获了什么？

测试配置成不让端点应答 store。CPU 请求因此一直挂起：日志先记录字节地址 `0x40`、数据 `0x40` 的 `DATA_WAIT`，到限定周期后仿真超时。测试通过是因为它抓到了一个一直有效、却没有完成的请求；它不能打印正常写入完成标志。这把“CPU 发起请求”和“目标完成事务”区分开。

## 运行与观察

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

第一个命令分别运行端点正常应答和 ACK 被抑制的真实 CPU 仿真。第二个命令是一个小型时序练习，用来理解请求/应答；它不能替代 CPU 仿真。

查看 `results/01/`、`results/01-no-ack/` 中的构建日志、运行日志、地址图和 VCD 波形。波形里可以依次看复位、CPU 的 AXI-Lite 请求、桥后的 Wishbone `cyc/stb` 和端点 `ack`。`cyc`、`stb` 同时有效表示请求有效；只有目标应答时事务才完成。

## PASS 能证明什么？

正常 PASS 表示 VexiiRiscv 从复位地址取指，并让端点观察到预期写入。`PASS 01-NO-ACK` 表示检查器发现请求没有 ACK；它不代表写入成功。第 02 章会单独验证从设备应答规则，让各种错误更容易定位。
