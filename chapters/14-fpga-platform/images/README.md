# 第 14 章布局布线图片

`tang20k-layout.png` 和矢量版 `tang20k-layout.svg` 来自已经完成布局布线的 `results/15-tang20k-build/routed.json`，对应第 14 章默认 Tang 27 MHz SoC。它们不是示意随机布局，也不是硅片显微照片。

- 左图：从单元的 `NEXTPNR_BEL` 读取真实 tile 坐标，按逻辑、触发器、存储、DSP、PLL、IO 着色。LUT 等同 tile 的槽位做微小偏移方便区分；不表示物理尺寸。
- 右图：从网络的 `ROUTING` 读取布线资源位置，按 tile 汇总占用出现次数，用对数颜色显示。它是布线资源密度图，不是每根导线的几何轨迹，也不是拥塞比例或时序裕量图。
- 图例是所选实际网表单元数量，排除了占位与常量辅助单元；存储类含块存储和分布式存储，不能把图例数字直接当 BSRAM 块数或存储字节数。

在仓库根目录重新生成：

```bash
python chapters/14-fpga-platform/images/render_layout.py
```

依赖 Python、NumPy、Matplotlib 和已有 `routed.json`、同目录 `summary.json`；不重新综合/布局布线，也不下载板子。`tang20k-layout.json` 保存输入哈希，便于追溯。脚本从输入目录的 summary.json 读取目标频率、CPU Fmax 估计和 seed，生成相应标注。

本机 nextpnr 的 SVG 原生导出在读入这个 routed JSON 时触发了器件坐标断言，因此使用独立脚本从实际结果提取数据。

## 27 MHz / 120 MHz 比较

```bash
python chapters/14-fpga-platform/images/render_layout.py \
  --compare results/15-tang20k-build-120mhz/routed.json \
  --output chapters/14-fpga-platform/images/tang20k-layout-27-vs-120mhz.png
```

默认输入为 27 MHz 版本。比较模式输出双行对比图，并更新同目录的 27 MHz、120 MHz 单独图片及 SVG/JSON。三张图共用坐标和颜色尺度，metadata 记录各输入哈希、目标、估计 Fmax、seed 和尺度。

120 MHz 使用既有结果，没有重新 P&R；其静态目标检查通过，尚未上板。两套系统的 PLL、UART、计数器等配置也不同，图中变化不能全部解释成时序目标单独造成的变化。

## 14E 最好 seed 2 的独立图片

```bash
python chapters/14-fpga-platform/images/render_layout.py \
  --input results/14e/best/routed.json.gz \
  --output chapters/14-fpga-platform/images/tang20k-layout-seed2.png
```

脚本直接解压已保存的真实布线结果，从同目录最终报告读取频率。输出 PNG、SVG 和来源哈希 JSON；不重新运行 nextpnr。seed 2 的目标为 150 MHz，系统域 Fmax 估计 147.21 MHz，仍为目标时序失败。本章 README 已用该独立图替换 120 MHz 对比图。
