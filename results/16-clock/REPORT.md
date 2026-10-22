# Tang Primer 20K clock

PASS：Yosys 综合、nextpnr 布局布线、Apicula bitstream。

器件 `GW2A-LV18PG256C8/I7`，数据库 `GW2A-18C`。27 MHz 时钟目标通过。

bitstream：`clock.fs`，SHA256 `bcb225126393769454c6997447e62f87ef4e583237b1d85adeccd924ea41bb81`。

上板：NOT_RUN，等待 USB 转交、识别与实际灯光观察。

## 实物下载

JTAG 识别通过，clock.fs 已下载到配置 SRAM。预期 010101 与 101010 两组灯约每半秒交换，实际观察等待用户反馈。
