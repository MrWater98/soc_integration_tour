# 19章实测结果怎么读

本次默认2KiB main RAM的结果在`results/19/`；缩为1KiB的独立结果在`results/19-small-ram/`。

| 配置 | CPU | main RAM | 全部Memory位数（含ROM） | 通用综合单元数 |
| --- | --- | ---: | ---: | ---: |
| 默认 | minimal / RV32I | 2048字节 | 52224位 | 49361 |
| 缩小容量 | minimal / RV32I | 1024字节 | 44032位 | 31632 |

容量减少1024字节，位数减少8192位；逻辑单元也会减少，但不是恰好减少8192个，因为读选择、写使能和地址逻辑会一起变化。这里的通用单元包含组合门和触发器，不能等同于触发器数量，更不是FPGA LUT数。

默认工艺映射使用18章固定的ICS55 RVT TT 1.2V/25°C库，映射统计面积为235567.92（Liberty面积数值之和）。没有物理布线、时钟树和pad ring，也未冻结die面积预算，所以不把它称为最终芯片面积。没有对1KiB配置重复工艺映射，不能给它编造一个同比例的工艺面积。

## 打开三份日志，确认不是只生成了网表

```text
simulation.log          过程展开RTL：UART=O,K；GPIO=9；PASS19
 generic-simulation.log 常量/触发器网表：同一套检查通过
 mapped-simulation.log  ICS55单元模型：同一套检查通过
```

默认运行记录为4338个TB周期，具体以各日志为准。不同综合表示的零延迟求值可能影响显示边界，不能将这段功能仿真直接用于芯片Fmax估计。

`pad-simulation.log`另有PASS_PAD，表示直接使用PDK PBMUX模型完成输入0/1和输出0/1/Z。这个结果和CPU的PASS19分开，因为尚未完成SoC pad ring绑定。

## 检查ROM是否真正进入了逻辑

打开`rtl/asic_soc.v`能看到.readmemh；打开`rtl/generic.v`、`rtl/mapped.v`则不应再依赖.init文件。它们已经把固件初值映射成固定逻辑，再用同一TB观察CPU执行成功。

检查`memory-inventory.json`时，不能只看main_ram：CPU寄存器堆也在里面。当前没有InstructionCache/DCache数组，是选minimal并实际检查后得到的事实。

## 哪些文件是输入、哪些只是报告？

- `rtl/*.v`和`.init`：当前表示的设计/模型输入，编译时按sources.json的原始源文件列表或选择单独网表。
- `synth.ys`、`map.ys`：Yosys实际执行的指令，可查看每步做了什么。
- `firmware/program.map`：变量、函数和链接符号地址，不是硬件译码器。
- `memory-inventory.json`：从Yosys存储对象提取的容量/端口/初值说明，不会创建RAM。
- `summary.json`：已执行检查的摘要及未完成项，不是配置输入。

本章README、HARDWARE_AND_BUILD和FIRMWARE分别从系统、硬件、软件解释这些文件之间的关系。
