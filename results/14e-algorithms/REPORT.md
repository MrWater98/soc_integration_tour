# 14E：布局布线算法与参数实验

使用同一份 16 KiB main RAM / 150 MHz 网表。先比较算法，再围绕有效参数扩大 seed 范围。

实际 48 次尝试，41 个完整时序结果，7 个工具错误，0 次超时。
150 MHz 通过 1 次；没有使用 timing-allow-fail，没有上板或打包 bitstream。

## 1. 共同 seed 2、5、8 的配置比较

| 配置 | 有效结果 | 最佳 MHz | 中位数 MHz | 150 MHz 通过 |
| --- | ---: | ---: | ---: | ---: |
| heap-default | 3/3 | 147.21 | 147.06 | 0 |
| heap-router1 | 3/3 | 147.21 | 147.06 | 0 |
| heap-router2 | 3/3 | 146.52 | 136.91 | 0 |
| heap-weight20 | 3/3 | 149.45 | 142.23 | 0 |
| heap-crit3 | 3/3 | 147.21 | 143.35 | 0 |
| heap-router2-ripup | 2/3 | 140.67 | 139.05 | 0 |
| heap-router2-alt | 3/3 | 140.02 | 139.82 | 0 |
| static-router2 | 0/3 | 无完整时序结果 | — | 0 |
| sa-router2 | 0/3 | 无完整时序结果 | — | 0 |
| heap-weight30 | 3/3 | 140.13 | 140.13 | 0 |
| heap-weight40 | 3/3 | 137.63 | 137.27 | 0 |
| heap-weight20-beta80 | 3/3 | 143.31 | 139.51 | 0 |
| heap-weight20-crit3 | 3/3 | 145.18 | 144.93 | 0 |

![相同 seed 的算法比较](algorithm-fmax.png)

## 2. 权重 20 扩展到 seed 1–12

前三个样本中权重 20 有改善，因此新增另外 9 个 seed。已有的 2、5、8 不重复计数。

| 指标 | 默认权重 10，seed 1–12 | 权重 20，seed 1–12 |
| --- | ---: | ---: |
| 最佳 MHz | 147.21 | 150.49 |
| 中位数 MHz | 140.57 | 141.72 |
| 150 MHz 通过 | 0/12 | 1/12 |

![相同 12 个 seed 的权重对照](weight20-seeds.png)

| seed | 权重 20 Fmax MHz | 状态 |
| --- | ---: | --- |
| 1 | 138.68 | TIMING_FAIL |
| 2 | 149.45 | TIMING_FAIL |
| 3 | 150.49 | PASS |
| 4 | 142.09 | TIMING_FAIL |
| 5 | 134.81 | TIMING_FAIL |
| 6 | 138.01 | TIMING_FAIL |
| 7 | 141.36 | TIMING_FAIL |
| 8 | 142.23 | TIMING_FAIL |
| 9 | 144.26 | TIMING_FAIL |
| 10 | 136.56 | TIMING_FAIL |
| 11 | 134.81 | TIMING_FAIL |
| 12 | 143.95 | TIMING_FAIL |

## 3. 本轮最佳实现的关键路径

最佳配置 **heap-weight20，seed 3，Fmax 150.49 MHz**。
起点 `VexRiscv.CsrPlugin_exceptionPortCtrl_exceptionValidsRegs_memory_DFFR_Q.Q`，终点 `VexRiscv.IBusCachedPlugin_cache.ways_0_tags.0.0.ADB6`。
路径 6.645 ns：路由 3.646 ns、逻辑 2.734 ns、clk-to-q 0.231 ns、setup 0.034 ns。150 MHz 预算约 6.667 ns。

这是有限样本中的最佳静态时序估计，不是板上最高频率。各 seed 的关键路径可能不同，不能把 Fmax 差值归因于同一条线的缩短。

## 4. 工具限制与结论

- 当前 Gowin 后端明确不支持 static 布局，三个 seed 都报错。
- sa 在本设计的初始布局阶段发生 SIGSEGV，三个 seed 都没有完整结果。
- router2 的实验性 tmg-ripup 在 seed 2 触发 base_arch.h:259 的断言；另外两个 seed 完成，但没有达到目标。
- 本组默认路由与显式 router1 的三个样本 Fmax 相同；router2 与 alternate weights 没有提升最好值。
- 权重 30、40 和降低密度的组合没有超过权重 20 的最佳结果。

时序权重改变布局优化的取舍；参数变大不保证更快，单个 seed 的改善也不代表所有 seed 都改善。

## 5. 文件之间的关系

- config.json / progress.json / summary.json / REPORT.md：初始九组的运行配置与汇总；本 REPORT.md 更新为完整实验报告，初始逐组数据仍在 summary.json。
- followup/：四组有针对性的参数调整，含独立配置、日志和汇总。
- weight20-extra-seeds/：权重 20 的另外九个 seed。
- campaign-summary.json：以上三个阶段的总汇；合计实际尝试次数、完整样本、错误、最佳实现和 12-seed 对照。
- 每组 input/：压缩网表、CST 和身份；rtl/：完整 HDL/初始化文件；seed-xxx/：实际命令、日志、最终报告、摘要。
- 每组 best/ 及根目录 best/：保留各组及全实验最佳实现的压缩路由、时序报告和摘要。
- analysis-command.json / analysis.log：重新解析 router2 日志的记录，不增加实际布局布线尝试次数。
- algorithm-fmax.* / weight20-seeds.*：由固定的 JSON 结果生成的科学绘图。

完整 routed.json 和解压网表保留本地，Git 保存压缩输入和最佳路线。每项最多运行 600 秒；共享主机并发会影响耗时，本文不做算法运行速度排名。三个阶段存在时间重叠，不把阶段墙钟简单相加作为总耗时。

## 6. 重现与重新汇总

执行命令和阶段参数见 [14E 教程](../../chapters/14e-seed-sweep/README.md#10-换布局布线算法在同一份电路上尝试不同解法)。完成三个阶段后：

```bash
python chapters/14e-seed-sweep/summarize_algorithms.py
python chapters/14e-seed-sweep/plot_algorithms.py --input results/14e-algorithms/campaign-summary.json
```

summarize_algorithms.py 验证各阶段的输入网表/CST 哈希一致后汇总，不运行 nextpnr。
