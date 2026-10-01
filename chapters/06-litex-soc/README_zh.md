# 06 — LiteX SoCCore 与 Builder

## 集成变更

使用 LiteX `SoCCore` 和 `Builder` 替换手工拼装的 SoC 外壳。CPU 注册、集成 ROM/SRAM、CSR 桥、总线互连、生成地址图和仿真工程交由 LiteX 管理。项目保留一个自定义 Wishbone 完成端点。

固件按 LiteX 地址图重新汇编：

| 区域 | 字节地址 | 容量 |
| --- | ---: | ---: |
| ROM | `0x00000000` | 4 KiB |
| SRAM | `0x10000000` | 4 KiB |
| 完成端点 | `0x80000000` | 4 KiB |
| CSR | `0xf0000000` | 64 KiB |

## CPU 总线自动适配

本章没有直接调用 `AXILite2Wishbone(...)`。CPU 提供 AXI-Lite pBus，而 SoCCore 主总线默认使用 Wishbone。LiteX 注册 CPU 主设备时，由 `add_master()` 调用 `add_adapter()`，再从协议转换表中实例化原生 `AXILite2Wishbone`。

```text
soc.py 选择 VexiiRiscv
    → SoCCore 使用默认 Wishbone 主总线
    → CPU AXI-Lite pBus 注册为 cpu_bus0
    → LiteX 实例化 AXILite2Wishbone
    → ROM / SRAM / 完成端点使用 Wishbone
```

LiteX 实现在 `litex/soc/interconnect/axi/axi_lite_to_wishbone.py`。构建日志应包含 `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit`。

## 运行与验收

```sh
PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py
```

运行器汇编本阶段固件，让 Builder 生成仿真工程和地址文件，核对生成区域，编译仿真器并运行 CPU。完成端点必须记录预期的末字写入。旧地址检查必须在仿真前拒绝之前手工地址图中的 SRAM 和完成端点地址。

输出写入 `results/06/`，包括 `csr.csv`、生成的软件文件、`memory_map.csv`、旧地址检查证据、构建/编译/运行日志和 VCD。

## LiteX 构建合同

- `soc.py` 定义 SoCCore 参数并接入完成端点。
- `vexii_config.py` 选择 LiteX 原生 VexiiRiscv standard，并关闭源码自动更新。
- `cpu_sim.py` 汇编固件并打包 ROM 镜像。
- `litex_builder.py` 调用 Builder、检查生成地址图并编译运行仿真器。
- 完成端点使用时序登记的 ACK。CPU 完成标记证明固件执行；生成地址图只证明 SoC 已构建。

软件地址图从阶段 05 起发生变化。每个 SoC 地址图都需要对应重新构建固件。
