# 14E：固定网表的 seed 实验

只改变 seed；目标、器件、网表和 CST 哈希固定。不使用 timing-allow-fail。

| seed | 状态 | 系统时钟域 Fmax MHz | 限制频率 MHz | 耗时秒 |
| --- | --- | ---: | ---: | ---: |
| 2 | TIMING_FAIL | 146.52 | 146.52 | 78.23 |
| 5 | TIMING_FAIL | 122.50 | 122.50 | 86.35 |
| 8 | TIMING_FAIL | 136.91 | 136.91 | 58.01 |

最佳 seed=2，本组最低时钟 Fmax 估计 146.52 MHz。150 MHz 目标通过 0/3。不是板上最高频率，也不是所有 seed 的全局最优。
