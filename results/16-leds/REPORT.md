# Tang Primer 20K leds

PASS：Yosys 综合、nextpnr 布局布线、Apicula bitstream。

器件 `GW2A-LV18PG256C8/I7`，数据库 `GW2A-18C`。纯组合固定输出，没有工作时钟。

bitstream：`leds.fs`，SHA256 `d8a486e2396a4cffd867bc45b498d440a042e86ae1c08edb97100322e825b3f9`。

上板：NOT_RUN，等待 USB 转交、识别与实际灯光观察。

## 反转图案下载

JTAG 识别通过，101100 已下载到配置 SRAM。LED5 到 LED0 预期灭、亮、灭、灭、亮、亮，实际观察等待用户反馈。
