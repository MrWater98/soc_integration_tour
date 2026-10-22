# 第 17 章及 SMP 本轮验收（2026-10-12）

| 实验 | 实测窗口 | 复位 | RAM 轮数下界 | RAM 读事务下界 | RAM 写事务下界 | IRQ 下界 | UART 回显 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 17-counted-hardware | 600.04 秒 | 0 | 388200 | 143384 | 1006736447 | 599956 | 1165 |
| 17-counted-resets | 60.01 秒 | 10 | 38500 | 19880 | 99849476 | 59444 | 117 |
| 17-counted-27mhz-hardware | 120.02 秒 | 0 | 39500 | 16952 | 103441466 | 119954 | 238 |

事务是主 RAM 从设备有效请求的 ACK 计数，缓存命中不包含在内；累计到最后一次日志。54 MHz 连续测试期间无复位；热复位另做。

- 17a：PASS: real SMP RTL and independent mailbox checks；2 次完整复位运行。
- 17a-parameters：PASS: real SMP RTL and independent mailbox checks；3 次完整复位运行。
- 17b：PASS: real SMP RTL and independent mailbox checks；2 次完整复位运行。
- 17b-delayed：PASS: real SMP RTL and independent mailbox checks；3 次完整复位运行。
- 17b-stop-hart：PASS: expected fault captured；2 次完整复位运行。
- 17b-bad-mailbox：PASS: expected fault captured；2 次完整复位运行。

完整 RTL/初值、源哈希、bitstream 哈希与时序见 summary.json 的 freeze 字段。小时级、物理冷启动、温压范围、SMP 上板、PLIC 外部中断和随机 SMP 长跑尚未验收。
