# Tang Primer 20K：开源构建

PASS：布局布线、nextpnr 目标 120 MHz 检查、bitstream 生成。

器件 `GW2A-LV18PG256C8/I7`，family `GW2A-18C`，seed 1。

bitstream 7261470 bytes，SHA256 `9f5b42d4eff65b6ce5344429405fd54276508aa726b244a774c9a58daec65318`。

| 资源 | 实际使用 | 可用 |
| --- | ---: | ---: |
| ALU | 594 | 15552 |
| BSRAM | 24 | 46 |
| DFF | 1680 | 15552 |
| LUT4 | 4457 | 20736 |
| MULT18X18 | 4 | 48 |

实际资源/时钟见 `summary.json` 的 report；原始日志 `nextpnr.log`。该检查不是 ASIC 签核；上板 SKIP，尚未拿到板子。
