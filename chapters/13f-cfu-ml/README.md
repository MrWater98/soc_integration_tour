# 13F（选学）：从一个神经元开始，用现成CFU加速计算

神经网络加速器并不一定一开始就是一个很大的NPU。我们先做一件看得懂的事：把几个乘法和加法交给硬件，再由真实RISC-V CPU调用它。

本章引入 **CFU Playground的原版四路INT8乘加核心**，使用LiteX现有CFU接口集成。先理解一个神经元，再做点积、两输出全连接层、软件/硬件对拍和计时。不会要求读者先掌握深度学习框架。

这是独立选学章节，不改变00–13必做主线、FPGA工程或ASIC规格。建议完成07章，了解C函数、ROM/RAM和启动之后阅读；不需要开发板。

## 从哪开始读？

| 阅读顺序 | 学什么 | 入口 |
| --- | --- | --- |
| 1 | 神经元、点积、权重、偏置、ReLU；为什么是13和[28,0] | [从算术理解算子](guides/01-math.md) |
| 2 | 四个8位数装进32位；有符号数与固定+128 | [数据怎样装进寄存器](guides/02-data.md) |
| 3 | 逐行读真实上游CFU，理解状态和握手 | [硬件逐行讲解](guides/03-hardware.md) |
| 4 | 逐段读main.c，看到普通C怎样发出自定义指令 | [C程序和指令](guides/04-software.md) |
| 5 | SoCCore参数、cpu_cfu、连接RTL、构建文件 | [LiteX集成与结果文件](guides/05-integration.md) |
| 6 | 看真实结果、故障、周期数，理解什么情况下会更快 | [实验记录与性能边界](guides/06-results.md) |

## 这次到底复用了什么？

上游固定提交：`7f8ec4147b39db98534f8a10f9ddb1c26aca5648`。

- `proj/proj_template_v/cfu.v`：最简单的直通CFU，先学接口，不做神经网络运算。
- `proj/dse_template/cfu.v`：四路有符号字节乘加，带固定输入偏移128和32位累加器。
- `common/src/cfu.h`及所需头文件：软件调用接口，最终编码CUSTOM0指令。

这些原版文件保存在本章upstream目录，保留许可和来源哈希。upstream/manifest.json记录精确来源，不是把我们自己写的乘加器冒充现成IP。

本地新增的是数学参考、测试平台、小型LiteX运行壳和教学文档。我们没有运行上游完整TensorFlow Lite Micro模型工程，也没有调用它的整个setup脚本。这样能先把一个算子和真实CPU调用讲清楚；日后再扩展完整模型。

原项目：[CFU Playground](https://github.com/google/CFU-Playground)。它的CFU不通过Wishbone收操作数，而是接在CPU的自定义指令接口上。

## 系统图：哪些走总线，哪些走CFU接口？

```text
                  ROM / RAM
                     ▲
                     │ Wishbone：取指、读输入、写结果
                     ▼
                  VexRiscv
               full+cfu变体
              ┌──────┴─────────┐
              │ 普通指令       │ CUSTOM0指令
              ▼                ▼
           CPU自身运算     CFU命令接口
                          两个32位操作数
                          10位功能编号
                               │
                               ▼
                       现成四路INT8乘加
                         32位累加器
                               │
                               └─响应 → CPU目标寄存器
```

RAM数据由CPU加载，再装入两个操作数寄存器。当前CFU不直接访问主存，没有DMA。Python配置SoC时也没有在Wishbone上给CFU分配一个地址。

## 直接运行

从教程根目录：

```sh
# 可选：下载并核对固定上游checkout，便于阅读完整工程
python chapters/13f-cfu-ml/fetch_upstream.py

# 本章完整实验：原版CFU测试 + 实际CPU硬件调用 + 软件模拟对照
python chapters/13f-cfu-ml/run.py
```

本章已携带所需上游小文件，所以运行实验不依赖external/CFU-Playground中其他Python逻辑。公共tutorial_paths只负责定位LiteX。工具需要前面已安装的RISC-V GCC、Verilator、C++、make和Icarus；优先使用OSS CAD Suite的Icarus/vvp。

只想学习CFU本身时，可运行：

```sh
python chapters/13f-cfu-ml/run.py --direct-only --vectors 257 --seed 7
```

它生成独立results/13f-direct，不覆盖完整CPU实验的摘要。本次参数组实际检查261组向量（4固定+257随机），背压和错误offset检查同样通过。

`--vectors`控制直接RTL实验的随机向量数，默认2000；另有4组固定向量，共2004。`--seed`默认13，决定随机输入和响应暂停长度。它们不改变硬件位宽、CPU内存容量或固件64组检查；固件随机种子0x12345678写在main.c中，若调整它或循环次数，应同步更新对拍数量和命令计数检查。

## 实验分成四步

```text
A 原版直通CFU：8个接口组合
   看懂valid/ready和两个输入如何选择
           ↓
B 原版乘加CFU：2004组向量
   对比Python独立参考，暂停响应0～7拍，测试复位恢复
   故意移除+128，确认检查能抓到错误
           ↓
C LiteX + 真VexRiscv + 原版CFU
   裸机C → CUSTOM0 → 硬件 → CPU结果
   点积13，全连接层ReLU后[28,0]，64组不同长度对拍
           ↓
D 同一C程序改用软件CFU模拟
   对比结果；硬件命令计数应为0，避免“以为用了硬件”
```

## 已实跑的结果

| 项目 | 当前结果 |
| --- | --- |
| 原版直通CFU | 8组检查通过 |
| 四路乘加 | 4组固定+2000组带seed随机向量通过 |
| 握手 | 响应暂停0～7拍时结果保持；消费后释放 |
| 复位 | 丢弃未消费响应、清累加器，下一次点积仍为13 |
| 错误offset负例 | vector=1即检测到不匹配 |
| 真CPU调用 | 点积13，两输出[28,0]，64组长度1～17对拍通过 |
| 硬件模式 | 实际接受619条CFU命令，静态代码有5处CUSTOM0 |
| 软件模拟模式 | 相同结果，CFU命令计数0，静态CUSTOM0数量0 |

实际记录在results/13f/summary.json。硬件模式日志在results/13f/run.log；软件模拟模式在results/13f-software/run.log。

**性能有一个重要结果：** 本次64次8元素点积，普通C耗10971周期，包含逐次打包的CFU调用耗24859周期；操作数预先打包就绪后的CFU循环耗727周期。先读[计时范围解释](guides/06-results.md)，再比较这些数字，不能把727周期当成整个网络推理的耗时。

## 参数和边界不要记成定值

| 数值 | 来源 | 改动时要核对什么 |
| --- | --- | --- |
| 4路×8位 | 所选上游CFU的具体RTL结构 | 打包函数、乘法位宽、参考计算和测试 |
| 输入偏移128 | 同一原版核心的localparam | 输入编码和参考公式，不是所有INT8网络都用128 |
| 32位累加器 | 核心状态宽度 | 溢出语义、最长点积范围 |
| 1～17元素 | 本章固件测试范围 | 尾部补齐，不是硬件规定最大向量长度 |
| 4KiB ROM/4KiB SRAM/16KiB main RAM | 本地LiteX运行壳配置 | 链接脚本、镜像大小、生成地址图 |
| full+cfu | 本地CPU包已有的带CFU变体 | ISA、缓存和CPU资源，不直接套用19章minimal结论 |
| 1MHz | 本章仿真时钟配置 | 周期到时间换算；不是FPGA/ASIC的最高频率结论 |

目前没有模型训练、卷积层完整实现、TFLM端到端推理、Gowin布局布线或板上加速结果。Tang Primer能否容纳所选完整系统，需要另做资源和时序测量。本章也不将full+cfu替换成已冻结的ASIC配置。

## 课堂回顾

1. `1×2+2×(-1)+3×3+4×1`为什么对应一个神经元里的主要计算？
2. 输入1为什么在这个CFU里先编码成0x81，而不是0x01？
3. 四个lane为什么按8位切分？修改成16位要改哪里？
4. funct7=1和funct7=0分别让累加器做什么？
5. rsp_ready=0时，为什么输出不能每拍继续累加？
6. CPU为什么需要带CFU的变体？普通标准RV32IM CPU会自动理解CUSTOM0吗？
7. 看到两个程序都输出13，怎样判断哪个真正用了硬件？
8. 为什么本次逐次打包版比普通C慢，预打包版却快？

可先独立作答，再读[答案与达标点](REVIEW.md)。
