# 14E：固定网表的 seed 实验

只改变 seed；目标、器件、网表和 CST 哈希固定。不使用 timing-allow-fail。

| seed | 状态 | 系统时钟域 Fmax MHz | 限制频率 MHz | 耗时秒 |
| --- | --- | ---: | ---: | ---: |
| 2 | TIMING_FAIL | 149.45 | 149.45 | 96.14 |
| 5 | TIMING_FAIL | 134.81 | 134.81 | 100.70 |
| 8 | TIMING_FAIL | 142.23 | 142.23 | 98.93 |

最佳 seed=2，本组最低时钟 Fmax 估计 149.45 MHz。150 MHz 目标通过 0/3。不是板上最高频率，也不是所有 seed 的全局最优。
