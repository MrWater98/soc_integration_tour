# Tang Primer 20K：开源构建

PASS：布局布线、nextpnr 目标 27 MHz 检查、bitstream 生成。

器件 `GW2A-LV18PG256C8/I7`，family `GW2A-18C`，seed 1。

bitstream 7261470 bytes，SHA256 `135f6ec11b34c6f38c3f3adcea5dc3717ad092266e1ab689bb092753b421410b`。

| 资源 | 实际使用 | 可用 |
| --- | ---: | ---: |
| ALU | 600 | 15552 |
| BSRAM | 24 | 46 |
| DFF | 1688 | 15552 |
| LUT4 | 4547 | 20736 |
| MULT18X18 | 4 | 48 |

实际资源/时钟见 `summary.json` 的 report；原始日志 `nextpnr.log`。该检查不是 ASIC 签核；上板 SKIP，尚未拿到板子。
