# Chapter 13 压力回归结果

状态：PASS；种子：1301
实际运行 10,108,365 个时钟；16 个场景；功能覆盖 44/44。

功能覆盖是本工具定义的场景清单；RTL 覆盖单独统计，保留未命中点。

## 未命中功能点

无

## RTL 覆盖

| 文件 / 类型 | 命中 / 总数 | 比例 |
| --- | --- | --- |
| VexRiscv.v:v_toggle | 7017 / 9617 | 72.96% |
| VexRiscv.v:v_line | 592 / 696 | 85.06% |
| VexRiscv.v:v_branch | 894 / 1008 | 88.69% |
| VexRiscv.v:v_expr | 136 / 180 | 75.56% |
| bus_monitor.v:v_toggle | 352 / 362 | 97.24% |
| bus_monitor.v:v_line | 16 / 16 | 100.0% |
| bus_monitor.v:v_branch | 15 / 16 | 93.75% |
| bus_monitor.v:v_expr | 46 / 66 | 69.7% |
| i2c_device.v:v_line | 17 / 17 | 100.0% |
| i2c_device.v:v_branch | 26 / 26 | 100.0% |
| i2c_device.v:v_toggle | 58 / 64 | 90.62% |
| i2c_device.v:v_expr | 20 / 21 | 95.24% |
| sim_control.v:v_toggle | 70 / 171 | 40.94% |
| sim_control.v:v_line | 28 / 29 | 96.55% |
| sim_control.v:v_branch | 19 / 30 | 63.33% |
| sim_control.v:v_expr | 25 / 39 | 64.1% |
| sim.v:v_line | 308 / 315 | 97.78% |
| sim.v:v_branch | 228 / 250 | 91.2% |
| sim.v:v_expr | 193 / 222 | 86.94% |
| sim.v:v_toggle | 2472 / 3407 | 72.56% |
