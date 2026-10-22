# 14E 固定网表 seed 实验结果

入口和完整过程见 [14E 教程](../../chapters/14e-seed-sweep/README.md)。本轮同一网表/CST、150 MHz 目标、seed 1–12，只改变 seed。

## 阅读顺序

1. config.json：器件、工具版本、目标、seed、并发与超时。
2. input/manifest.json：固定输入的来源与哈希；netlist.json.gz 是保存的综合网表，CST/平台配置也在 input。
3. rtl/：实际完整 HDL/初值快照，帮助查看输入电路；本轮实际运行的是冻结网表。
4. seed-*/command.json、nextpnr.log、pnr-report.json、summary.json：每次命令、完整运行证据、最终路径和频率。
5. summary.json：所有结果、最好/最差/中位数、总耗时。system_fmax_mhz 是共享 sys 时钟域的估计，不只衡量 CPU 内部。
6. REPORT.md、seed-fmax.png：可读实验过程与图表。
7. best/：seed 2 的最终报告、摘要、压缩布线数据。

最好估计为 147.21 MHz，最差 117.47 MHz，中位数 140.57 MHz；150 MHz 通过 0/12。全程未打包或下载板子，没有物理频率测量。

原始网表和各次完整 routed.json 是本地工作文件；压缩的固定输入、最优结果、完整 RTL 与各次报告/日志纳入保存。使用 --replay 可以读取保存的输入，重跑前注意独立目录，避免覆盖历史记录。
