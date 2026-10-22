# Tang Primer 20K Dock：无板卡准备

PASS：完整 RTL、ROM 镜像、7 个管脚、电平、PLL 和内存图检查。

参考时钟 27000000 Hz；系统时钟 2.7e+07 Hz；UART 115200 baud。

CST 两项故障注入均被捕获；RTL 可独立展开；心跳与同步逻辑仿真通过。

上板：SKIP，板子尚未到货；第 15 章负责综合/布局布线/bitstream。

## 数字集成仿真

PASS：真实 VexRiscv 执行固件，经真实 UART TX 引脚解码；按钮值 0→1→0、LED5 对应变化、复位后再次 HELLO。PLL 使用理想 27 MHz 仿真替代模型，不验证模拟锁定行为。
