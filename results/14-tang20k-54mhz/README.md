# 14-tang20k-54mhz：Tang Primer 20K 生成结果

这是第 14 章 `tang_run.py` 生成的电路、软件接口与 ROM 初值。它还不是下载文件；后续综合/布局布线和实物记录分别在第 15、16、17 章。

## 本目录的配置

| 参数 | manifest 中的值 |
| --- | --- |
| `reference_clk_hz` | 27000000 |
| `sys_clk_hz` | 54000000 |
| `baud` | 115200 |
| `rom_size` | 8192 |
| `sram_size` | 4096 |
| `main_ram_size` | 16384 |
| `stack_size` | 1024 |
| `por_cycles` | 65536 |

存储/栈容量单位为字节，时钟单位为 Hz；这些是本目录的配置，不是所有 SoC 的固定要求。准确 PLL 编码、球位和源哈希请读 `manifest.json`。

## 怎么读这些文件？

1. `manifest.json`：核对身份、时钟与容量。
2. `builder/software/include/generated/csr.h`：读 C 访问函数及地址。
3. `firmware/linker.ld`、`program.map`、`program.elf`：检查 C/启动代码的内存布局与实际指令。
4. `rtl/tutorial14.v`：读顶层端口、层级、CPU/PLL 实例、CSR/GPIO 连接。
5. `rtl/tutorial14_rom.init`：对照 ROM 内容与固件；同目录还保存所有模块/初值和来源清单。
6. `constraints/tutorial14.cst`：检查端口球位和 IO 标准。
7. `summary.json`：逐项区分生成、展开、局部逻辑与约束检查。

`builder/`、`firmware/` 中的许多本地产物未纳入 Git；需要时在仓库根目录运行第 14 章生成命令。`rtl/` 是已保存的完整快照。

完整解释见 [14.3：结果逐项解读](../../chapters/14-fpga-platform/guides/03-results/README.md)，软件地址到引脚的场景见 [14.4：操作跟踪](../../chapters/14-fpga-platform/guides/04-walkthrough/README.md)。

旧 `onboard` / `board_revision` 字段可能仍写未到货，是当时生成步骤留下的文案，不会自动跟踪当前板卡状态；准确实物进度看对应上板日志。目录中有 RTL 或 `status=PASS`，都不能单独证明该频率已经在板上运行。
