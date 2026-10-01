# 04 — 可写 SRAM 与栈区

## 集成变更

在字节地址 `0x00010000` 接入 4 KiB Wishbone SRAM。CPU 从 ROM 启动，访问 SRAM 首末字，执行字节和半字写入，并使用 SRAM 作为函数调用栈。

固件在全字和部分字节通道写入后，预期首字读回 `0xbbcc33aa`。它还在末字地址 `0x00010ffc` 写入并读回数据，最后通过寄存器端点报告完成。

## 运行与验收

```sh
PYTHONHASHSEED=0 python3 chapters/04-sram/run.py
```

运行器分别执行正常的 4 KiB 配置和负例 256 字节配置。正常场景必须以预期读回值完成。小容量场景必须报告 `mcause=7`（store access fault）及预期故障标记，且不能出现正常完成标记。

输出写入 `results/04/` 和 `results/04-small-ram/`，包括 ROM/RAM 镜像、地址图、运行日志和 VCD 波形。

## 存储与 ABI 约束

- SRAM 是 LiteX Wishbone 行为模型。替换为 FPGA block RAM 或 ASIC SRAM 宏时，需要匹配端口宽度、读延迟、写掩码和初始化行为。
- 本集成中的 Wishbone `adr` 按字寻址。字节地址 `0x00010000` 对应字地址 `0x4000`。
- 栈从配置的高地址向下增长。固件显式调整 `sp`，在嵌套调用前把 `ra` 保存到 SRAM，返回前恢复，并维持栈对齐。
- 栈空间与末字边界检查使用互不重叠的 SRAM 地址。
