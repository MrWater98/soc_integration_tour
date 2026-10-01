# SoC 集成实践

这个项目从一个很小的系统开始，逐步看清 SoC 是怎样接起来、怎样验证的。当前使用 LiteX 和单核 VexiiRiscv，00–06 章已经实现并可运行。每章的硬件逻辑放在本章目录中；中文说明对应各章的 `README_zh.md`。

## 为什么要一步步搭？

用 LiteX、HeteroSoC 或 Chipyard 很快就能拼出一个能运行的 SoC。我还想弄清每个部件究竟做了什么：哪个参数选择 CPU，总线请求由谁回答，汇编如何变成 ROM 镜像，软件地址怎样到达目标硬件。完整系统会把不少边界藏进生成的 RTL 里，所以这个项目先把问题拆开，再用 LiteX 把系统装回来。

每一步只回答一个主要问题：跑一个正常案例；需要时再制造一个可控的错误；保存地址图、固件、日志和波形。配置生成成功与 CPU 真正执行固件是两件事，分别检查。

## 00–06 章

| 章节 | 要回答的问题 | 运行命令 |
| --- | --- | --- |
| 00 环境 | 哪些包和工具分别生成 CPU RTL、固件和仿真器？ | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU 启动 | 原生 VexiiRiscv 能否退出复位、取 ROM 指令并发出指定写入？ | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | 怎样才算一次请求完成？缺少或错误 ACK 怎样被抓到？ | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | 汇编、ELF、二进制字节、hex 字、复位地址和 ROM 容量如何对应？ | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | 可写内存怎样工作？为什么 `sp` 要变化，嵌套调用前要保存 `ra`？ | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 地址图 | 每个地址由哪个设备回答？地址重叠或落在空洞里会怎样？ | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`、`Builder` 和 LiteX 原生 AXI-Lite 到 Wishbone 桥各自做什么？ | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |

所有命令都从项目根目录运行。生成文件放在 `results/`，该目录被 Git 忽略，因此日志、波形和构建文件保留在本地。

## 从源码到总线应答

```text
program.S ── RISC-V GCC ──> ROM 镜像 ──> VexiiRiscv 执行固件
                                           │ AXI-Lite 外设总线
                                           ▼
                               LiteX AXILite2Wishbone
                                           │ Wishbone 主总线
                             ┌─────────────┼─────────────┐
                             ▼             ▼             ▼
                            ROM          SRAM          寄存器端点
                                           │
                            LiteX Builder 生成地址图
```

这里有两条相关的路径：Builder 构造硬件并导出地址图；之后 CPU 才通过构造好的硬件发出真实事务。地址检查会比较生成的地址表和固件使用的地址。

## 贯穿项目的问题

### Migen 是 LiteX 的一个模块吗？

Migen 是独立的 Python 硬件描述库。LiteX 建立在 Migen 之上，用它描述和连接 SoC 硬件。LiteX 工程会用到 Migen 模块，但两者是分别安装、分工不同的项目。

### LiteX 原生支持 VexiiRiscv 吗？

本项目固定的 LiteX 版本里有原生 VexiiRiscv 封装，注册名是 `vexiiriscv`，这里选择 `standard` 变体。封装定义 CPU 怎样接入 LiteX；VexiiRiscv 的 Scala/SpinalHDL 生成器负责产生 CPU RTL，由 `sbt` 执行。

### `AXILite2Wishbone` 是我们写的吗？

不是。VexiiRiscv 对外的外设总线是 AXI-Lite，本项目 SoC 的主总线是 Wishbone。LiteX 注册 CPU master 时发现两种接口不同，会插入原生 `AXILite2Wishbone` 桥。第 06 章会讲它的代码路径，并检查构建日志中的适配信息。我们自己写的是 Wishbone 端点，不是协议桥。

### 为什么地址有字节地址和字地址？

固件和生成的 memory map 使用字节地址。这里的 32 位 Wishbone 接口按字寻址，每加一表示 4 字节。例如软件地址 `0x40` 在 Wishbone 上显示为字地址 `0x10`。比较固件、地址表和总线波形时，先确认数值使用的单位。

### ACK 表示什么？

Wishbone 请求期间 `cyc` 和 `stb` 有效；从设备给出 `ack`，表示这笔请求已经完成。即使 `dat_r` 上有数值，没有 ACK 也不能算一次完整读操作。第 02 章逐周期记录信号，让无应答、提前应答、ACK 悬挂和错误地址都能对应到具体证据。

### CPU 为什么需要栈？

`sp` 是软件维护的 RAM 字节地址，用来标记当前分配的栈空间。`jal` 会把返回地址写入寄存器 `ra`；嵌套调用会覆盖它。函数还需要旧返回地址时，就先把它保存到自己的栈帧，返回前再恢复。CPU 不会自动把所有参数和返回地址压栈；具体保存哪些值由程序和 ABI 决定。

### 这里的 SRAM 是真实宏吗？

04–06 章在仿真中使用 LiteX 的 Wishbone 行为 SRAM，用来检查总线可见的读写、字节使能和固件访问。FPGA 实现还要把它映射到芯片内的 block RAM 等资源，并检查实际延迟和时序。ASIC SRAM 宏通常使用原生存储器引脚，不直接说 Wishbone；需要一个包装模块把总线请求转换成宏的控制信号，并在宏返回后发 ACK。

### 生成的地址图能证明什么？

它能证明 LiteX 构造了哪些地址区域、起点和容量，但不能证明 CPU 已执行程序。第 06 章先检查 Builder 生成的地址图，再运行仿真并要求 CPU 写出完成标志。两类证据都要有。

## 阅读顺序

从[第 00 章](chapters/00-environment/README_zh.md)开始，按编号阅读。每章都说明当前要解决的问题、数据/总线路径、运行方法、预期证据，以及 `PASS` 能证明到什么程度。[PLAN.md](PLAN.md)记录后续计划；07–15 章目前还没有实现。
