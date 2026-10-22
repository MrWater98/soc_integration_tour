# 17-acceptance：已执行案例与固定输入的汇总

完整实现解释见 [对应章节 README](../../chapters/17-fpga-stability/README.md)。本文件说明这个结果目录的用途；它不会重跑实验或改变已有统计。

## 这里为什么没有新的 .fs？

这个目录由验收整理步骤把已经执行的板上/SMP 案例和冻结身份汇总到 `summary.json`，不是另外创建了一套 FPGA 电路。`REPORT.md` 展示实测时长、读写/IRQ/回显计数；summary 的 `cases` 保存原案例结论，`freeze` 保存完整 RTL/配置/bitstream 身份，`pending` 列出未测项。

其中 54 MHz 连续 600 秒、27 MHz 连续 120 秒和热复位是已执行的记录；一小时、温压范围、物理冷启动和 SMP 上板仍未执行。不能把汇总 PASS 理解为所有计划已通过。
