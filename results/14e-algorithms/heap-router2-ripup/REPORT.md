# 14E：固定网表的 seed 实验

只改变 seed；目标、器件、网表和 CST 哈希固定。不使用 timing-allow-fail。

| seed | 状态 | 系统时钟域 Fmax MHz | 限制频率 MHz | 耗时秒 |
| --- | --- | ---: | ---: | ---: |
| 2 | TOOL_ERROR | 0.00 | 0.00 | 107.30 |
| 5 | TIMING_FAIL | 140.67 | 140.67 | 165.41 |
| 8 | TIMING_FAIL | 137.44 | 137.44 | 185.35 |

最佳 seed=5，本组最低时钟 Fmax 估计 140.67 MHz。150 MHz 目标通过 0/3。不是板上最高频率，也不是所有 seed 的全局最优。
