# 14E：main RAM 从 16 KiB 缩到 4 KiB

## 结论

150 MHz 未通过：12 个 seed 全部完成路由，0/12 满足时序，没有工具故障或超时。最佳 seed 8 的共享系统域 Fmax 为 **142.35 MHz**；原来 16 KiB 配置最佳 seed 2 为 **147.21 MHz**。板上验证和 bitstream 打包未执行。

| 项目 | 原配置 | 缩小配置 |
| --- | ---: | ---: |
| main RAM | 16 KiB | 4 KiB |
| ROM / 额外 SRAM / 栈预留 | 8 / 4 / 1 KiB | 8 / 4 / 1 KiB |
| 块 RAM 原语数量（综合网表） | 24 | 18 |
| 映射单元总数（不同类型合计） | 6238 | 6338 |
| 最佳 Fmax MHz | 147.21 | 142.35 |
| 中位数 MHz | 140.57 | 131.62 |
| 150 MHz 通过 | 0/12 | 0/12 |

块 RAM 统计合计 SP/SPX9、DPX9B、SDPX9B；不含分布式 RAM16SDP4。main RAM 本身从 8 个 SP 减为 2 个 SPX9，其他块 RAM 数量保持不变。块 RAM 容量/模式不同，单元总数也不能当作芯片面积或 LUT 数。

## 为什么节省 RAM 却没有更快？

容量改变后，地址译码、内存实现和逻辑优化发生变化，布局搜索面对的是另一份网表。栈顶移动也改变了启动指令和 ROM 初始化。资源数量下降不保证最长路径变短，原来的最佳 seed 编号也不会自动成为新网表的最佳编号。

新最佳路径从 `DBusCachedPlugin_exceptionBus_payload_code` 寄存器出发，到指令缓存 tag RAM 的 `ADB6` 地址端。总延迟约 7.025 ns，其中路由 3.629 ns、逻辑 3.131 ns，clk-to-q/setup 合计 0.265 ns。150 MHz 预算为 6.667 ns，约差 0.358 ns。最慢路径位于 CPU 的异常/缓存控制相关网络，不是 main RAM 容量本身；若继续冲击 150 MHz，需要研究这些具体路径。

这些结果只比较各自的 12 个 seed，不代表所有可能布局的极限，也不说明每个小内存设计一定更慢。

## 功能检查

同容量的 27 MHz 版本运行真实 CPU/UART 数字仿真：启动 HELLO、按钮 0→1→0、LED 响应、复位后再次 HELLO 均通过。PLL 是理想替代模型。150 MHz 版本完成 RTL 生成、引脚/映射检查、Yosys 综合和静态时序检查。

链接结果 `.data`、`.bss` 都为 0 字节；栈预留 1 KiB，栈顶 `0x40001000`、栈底 `0x40000c00`。本测试通过不等于已测量所有未来固件的最大栈深度。

## 文件如何产生？

- `platform/`：150 MHz / 4 KiB 配置，经 tang_run.py 生成完整 RTL、初始化文件、C 固件链接映射、CST 和配置身份。
- `functional/`：27 MHz / 4 KiB 配置，同一构建入口生成，再由 sim_tang.py 执行功能检查；digital-sim.log 与 digital-summary.json 是证据。
- `synthesis/`：第 15 章 Yosys 入口读取 platform/rtl，产生综合日志、资源统计、网表及完整 RTL 副本。
- `sweep/input/`：冻结并压缩综合网表，保存 CST 和输入哈希。netlist.json 是本地解压工作文件。
- `sweep/seed-001` 到 `seed-012`：每项实际命令、nextpnr 日志、最终时序报告及摘要。完整 routed.json 留在本地。
- `sweep/best/`：seed 8 的最终布线压缩快照和报告。
- `comparison.json`：旧/新配置的对比数据；`sweep/summary.json`：本组完整结果。

完整命令见 [14E 教程](../../chapters/14e-seed-sweep/README.md#9-缩小-main-ram容量减少会让时序更好吗)。本组总墙钟 429.49 秒，并发两个进程，每项超时限制 180 秒，没有使用 timing-allow-fail。

每个 seed 的完整结果见 [扫描报告](sweep/REPORT.md)。
