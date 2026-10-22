# Tang 150 MHz 构建输入

本实验由第 14 章 `tang_run.py --sys-clk-hz 150000000` 生成，软件实验上限扩展到 150 MHz；它不是器件最高工作频率的声明。

参考输入仍为 27 MHz，系统目标为 150 MHz。PLL 配置为 idiv=9、fdiv=50、odiv=8、VCO=1200 MHz；固件、CSR 地址、顶层和 ROM 初值在本目录配套生成。

生成与展开结果看 summary.json；实际综合在 ../15-tang20k-150mhz，布局布线及目标检查在 ../15-tang20k-build-150mhz。生成通过不能算时序通过，本实验不下载板子。
