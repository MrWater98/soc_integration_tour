# 第 15 章：开源 FPGA 综合

PASS：完整 SoC 已映射到 gw2a 原语；check -assert 通过。

Yosys 0.69+272 (git sha1 230fb23f8, Release, Clang /usr/bin/clang++ 21.1.8)

| 原语 | 数量 |
| --- | ---: |
| ALU | 546 |
| DFF | 171 |
| DFFE | 1125 |
| DFFP | 2 |
| DFFR | 122 |
| DFFRE | 219 |
| DFFS | 35 |
| DFFSE | 14 |
| DPX9B | 6 |
| GND | 1 |
| IBUF | 4 |
| LUT1 | 459 |
| LUT2 | 626 |
| LUT3 | 953 |
| LUT4 | 1470 |
| MULT18X18 | 4 |
| MUX2_LUT5 | 791 |
| MUX2_LUT6 | 152 |
| MUX2_LUT7 | 50 |
| MUX2_LUT8 | 10 |
| OBUF | 3 |
| RAM16SDP4 | 4 |
| SDPX9B | 4 |
| SP | 8 |
| SPX9 | 6 |
| VCC | 1 |
| rPLL | 1 |

布局布线、时序与 bitstream：NOT_RUN；上板：SKIP。
资源数来自综合网表，不是布局布线后的资源占用或时序结论。
