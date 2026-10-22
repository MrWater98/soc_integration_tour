# 17-counted-27mhz：固件和电路构建输入

完整实现解释见 [对应章节 README](../../chapters/17-fpga-stability/README.md)。本文件说明这个结果目录的用途；它不会重跑实验或改变已有统计。

## 这套输入是什么？

| 参数 | 本次值 |
| --- | --- |
| `sys_clk_hz` | 27000000 |
| `baud` | 115200 |
| `rom_size` | 8192 |
| `main_ram_size` | 16384 |
| `stack_size` | 1024 |
| `stress_words` | 512 |
| `seed` | 1 |
| `inject_fault` | False |

频率单位 Hz、容量单位字节；stress_words 是 32 位字数，不是 RAM 总容量。

## 文件来源与使用顺序

1. `manifest.json`：build.py 写出电路参数、PLL 和快照身份。
2. `builder/csr.csv` 与 `software/include/generated/`：Builder 从本章硬件生成地址图和软件接口。
3. `firmware/`：本章生成链接布局/测试头文件，GCC/objcopy 输出 ELF、map、bin；这些文件决定 ROM 指令和数据/栈位置。
4. `rtl/`：本章收集顶层、CPU、所有初值和原语；sources.json 记录角色和哈希，files.f 供展开检查使用。
5. `constraints/tutorial14.cst`：本章 tutorial17.cst 的复制件，旧名字不代表引用另一章电路。
6. `synthesis/`：Yosys 脚本、输入副本、网表、综合报告。
7. `build/`：nextpnr 位置/布线/时序报告，Apicula 打包的 tutorial17.fs。run.py 用它下载，先核对 bitstream 哈希。
8. `freeze.json`：若存在，是验收整理时另外写出的固定输入记录，不是每次生成的默认输出。

许多中间产物和 .fs 没有提交 Git，需要时重新构建。已有构建 REPORT 的“不执行实物”说明只针对构建步骤，实物结论在独立硬件运行目录。
