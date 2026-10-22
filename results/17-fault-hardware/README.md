# 17-fault-hardware：主机保存的真实板卡运行记录

完整实现解释见 [对应章节 README](../../chapters/17-fpga-stability/README.md)。本文件说明这个结果目录的用途；它不会重跑实验或改变已有统计。

## 哪套电路在运行？

主机的 `--input` 为 `results/17-fault`，此处保存观察结果。`parameters` 是主机命令参数；硬件参数在输入目录的 manifest。

| 文件 | 生产者与作用 |
| --- | --- |
| `detect.log` | 主机保存 openFPGALoader 探测输出；使用 --load 时产生 |
| `load.log` | 主机保存 SRAM 下载输出 |
| `uart.log` | 主机按换行保存真实 UART 内容，前缀是主机时间 |
| `summary.json` | run.py 按 BOOT、进度、回显、故障与超时规则汇总 |
| `REPORT.md` | summary 的人读摘要 |

- `status`：PASS: injected RAM error captured
- `clock_hz`：54000000
- `elapsed_seconds`：0.005123285984154791
- `boots`：1
- `warm_resets`：0
- `echoes`：0
- `fault_caught`：True

max_rounds/max_irqs 是最大单阶段值，total 字段才按阶段累计；累计到最后一次日志，是下界。旧报告没有新字段，不代表已测值为零。温压/冷启动未测项应读对应字段，不能由数字压力 PASS 推断。

本负例捕获的是 `17 FAIL code=10000100`，即默认数组下标 256 的位翻转。实验在捕获后提前结束，所以不要求运行满请求的最大时长或完成正常回显门槛。
