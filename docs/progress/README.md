# 从仿真 SoC 到 FPGA，再到 ASIC：当前进度

这份说明是本次同步的阅读入口。tour 的 00–12 章保留原实验实现，文档按连续技术讲解组织；从 13 章起，补入 tutorial 已经实现的实验、讲解与结果。完整路线见 [PLAN](../../PLAN.md)，实际可运行到 20 章及 20A 教学分支。PLAN 后面的流片、封装、硅后章节仍是计划。

## 整个项目到底走到了哪里？

```text
00–12：CPU 从 ROM 启动，访问 RAM 和外设
   │
13：把各部分接成整机，用自检和故障注入验证
   ├── 13A/B：通过 JTAG 串行入口访问寄存器、观察/接管边界引脚
   ├── 13C/D：OpenOCD 与 GDB 分别做实验，尚未连成 CPU 在线调试系统
   └── 13F：把神经网络的一个小算子接到 CPU 自定义指令接口
   │
14–16：同类 SoC 适配 Tang Primer 20K，经开源工具构建并在实物运行
   ├── 14E：保持输入固定，研究布局布线参数怎样影响最高频率
   │
17：板上压力、事务计数、复位与长跑
   ├── 17A/B：单 hart / 双 hart SMP 仿真
   │
18：接入 ICS55 PDK，先验证最小标准单元流程
   │
19：换成适合 ASIC 试验的小核心，明确每一块存储如何实现
   │
20：检查故障、复位、随机事务、有限步属性、时钟连接与行覆盖
   └── 20A：用小电路实验理解扫描链、RAM March 和故障检测
   │
后续：真实 RAM 宏、生产 DFT、物理设计、签核、流片和硅后验证
```

这条路径中的设计配置会改变。例如 FPGA 板上工程、SMP 工程、19 章的小型 ASIC 工程不是同一份网表。频率、缓存、RAM 容量、GPIO 位数都要以当前实验参数和结果为准。

## 已经做了哪些实验？

| 阶段 | 做了什么 | 去哪里看证据 | 仍需补什么 |
| --- | --- | --- | --- |
| [13 整机](../../chapters/13-integration/README.md) | 八项串口自检、IRQ/协议/存储并发，错误地址和损坏 ROM 等失效情境 | 对应章节的运行说明、`results/13` 的 RTL 快照；完整日志可重新运行生成 | 更长时间和更多配置的整机覆盖 |
| [13A TAP](../../chapters/13a-jtag-tap/README.md)、[13B 边界扫描](../../chapters/13b-boundary-scan/README.md) | TAP 状态、捕获/移位/更新、引脚采样、输出接管与数字故障 | `results/13a`、`13b` 的 summary、pins.html、CSV | 目标 ASIC 的实际边界单元和完整引脚链 |
| [13C OpenOCD](../../chapters/13c-openocd/README.md)、[13D GDB](../../chapters/13d-gdb/README.md) | OpenOCD 经模拟适配器访问 TAP；GDB 调试本机递归程序 | `results/13c`、`13d` | 将 GDB、RISC-V 调试模块、CPU 控制真正连起来 |
| [13F CFU](../../chapters/13f-cfu-ml/README.md) | 固定上游四路 INT8 MAC，真实 CPU CUSTOM0 调用、C 对拍、计时、背压/复位/错误偏移负例 | `results/13f/summary.json`，另有纯软件和独立 RTL 对照 | 完整 TFLM 模型、FPGA 和 ASIC 实现 |
| [14 平台](../../chapters/14-fpga-platform/README.md)至[16 上板](../../chapters/16-board-smoke/README.md) | Tang Primer 20K Dock，Yosys 综合、nextpnr 布局布线、Apicula 生成 .fs，下载后收到 HELLO/ALIVE | `results/14-tang20k`、`15-tang20k-build`、`16-tang20k` | 此处复制了原实物记录，尚未从 tour 重新下载 |
| [14E 参数搜索](../../chapters/14e-seed-sweep/README.md) | seed、RAM 容量、布局算法及权重实验 | `results/14e`、`14e-small-ram`、`14e-algorithms` | 最高频率配置的实物验证 |
| [17 稳定性](../../chapters/17-fpga-stability/README.md) | 54 MHz 连跑 600 秒、10 次热复位；27 MHz 连跑 120 秒，记录硬件 RAM 已完成事务 | `results/17-counted-hardware`、`17-counted-resets`、`17-counted-27mhz-hardware` | 小时级、温度/电源范围、物理冷启动 |
| [17A 单 hart](../../chapters/17a-smp-single/README.md)、[17B 双 hart](../../chapters/17b-smp-dual/README.md) | 真实 SMP RTL 的栈、邮箱、原子更新、CLINT 与多次复位 | `results/17a`、`17b*` | SMP 上板；Linux 仍未跑通 |
| [18 PDK](../../chapters/18-ics55-spec/README.md) | 固定 ICS55 版本；最小计数器映射、工艺功能模型仿真、TT 单角 STA | `results/18/summary.json` | 完整 SoC 的物理实现和多角签核 |
| [19 ASIC RTL](../../chapters/19-asic-rtl/README.md) | 无缓存 RV32I；存储清单、常量 ROM/触发器 RAM、通用与 ICS55 网表启动、IO 模型小实验 | `results/19`、`19-small-ram` | 真实 SRAM 宏、pad ring、封装约束和物理时序 |
| [20 验证](../../chapters/20-asic-verification/README.md) | 多次启动、故障、随机外设、复位、12 步形式检查、lint、时钟连接与行覆盖 | `results/20/summary.json`、覆盖报告和日志 | 顺序等价、专用 CDC/RDC、覆盖收敛、长时整机压力 |
| [20A DFT](../../chapters/20a-dft-basics/README.md) | 小计数器内部扫描、RAM March、卡死与地址别名故障 | `results/20a`、`20a-parameters` | 向真实 SoC 插入扫描、ATPG、真实宏 MBIST |

## 几个结果怎样读？

**13F：加速器不是接上就一定更快。** 独立 RTL 检查 2004 组向量；真实 CPU 的点积为 13，全连接加 ReLU 输出 `[28, 0]`，64 组不同长度检查通过，记录到 619 次命令和 619 次响应。64 次重复的标量参考是 10971 周期；每次打包再调用 CFU 是 24859 周期；预打包是 727 周期。最后一个数不包含打包成本，不能当作完整推理加速比。

**14E：布局后的 Fmax 是该次工具结果。** 原 16 KiB RAM 配置在 heap 时序权重 20、seed 3 下达到约 150.49 MHz，满足 150 MHz 的静态约束。这不等于该配置已经在板上以此频率长期工作。缩小 RAM 的实验也没有必然更快，布局、扇出和关键路径同样重要。

**19：存储已经有实现，但还没换成 SRAM 宏。** 默认 ROM 4 KiB、片上 SRAM 256 B、main RAM 2 KiB，再加 CPU 寄存器堆，共 52224 bit 的数组清单。RAM 映射成触发器、ROM 优化成常量逻辑，ICS55 映射有 68368 个标准单元实例。这适合先验证流程；真实宏的面积、端口和时序需要另外评估。1 KiB 工作 RAM 是独立参数实验，没有做该组 ICS55 映射。

**20：通过的范围写在分母和检查类型里。** 随机外设共 30000 次请求，其中 267 次被复位中止、29733 次完成。形式检查只覆盖 12 步限定的安全属性；错误 ACK 版本能被识别。纯行覆盖中，至少一个关联计数点命中的行是 1854/2073（89.44%）；要求一行全部关联点都命中是 1770/2073（85.38%）。这不是所有 CPU 行为都验证完毕。

**20A：故障检测率只针对本实验列举的故障。** 四位计数器的 8 个卡死故障，正常输出检测 2 个，扫描检测 8 个。默认 8×8 RAM 的 19 个数据/地址故障全部检测；这不是生产芯片的 ATPG 覆盖率。

## 怎么看文件之间的关系？

```text
章节 Python + 自带 RTL          startup.S + main.c + linker.ld
          │                                │ GCC / objcopy
          │ LiteX / Migen                   ▼
          ├────────────────────────── 固件镜像 / map / 反汇编
          ▼                                │
results/<实验>/rtl/ ◄─────────────── ROM 初始化文件
          │
          ├── 仿真器 + tb ─────────────── 日志 / CSV / 波形
          └── Yosys ─ 通用网表 ─ 工艺映射 ─ 网表仿真
                                           │
                                    summary.json / REPORT.md
```

- `chapters/` 放讲解、构建脚本、固件源码、约束和测试平台。新章节的 Python 逻辑保存在各自目录中。
- `results/*/rtl/` 是完整输入快照；Verilog 中若有 `$readmemh`，相应 `.init` 也属于输入，不可漏掉。
- `summary.json` 是机器可读结论；先看 `status`、参数、未执行项，再顺着日志定位原因。
- `REPORT.md` 是较短的人类可读结果；更详细的原因在章节文档里。
- `firmware/program.map` 回答“段和符号在哪”，反汇编回答“CPU 执行哪些指令”。
- 临时编译目录、波形、大型中间 JSON 和下载的工具不随本次同步复制；运行脚本可重建。历史日志中的旧绝对路径保留为原始证据。

关于 `csr.h`、`soc.h`、`mem.h` 和 Builder 的文件生成关系，单独阅读[生成文件说明](../generated-files/README.md)。

## 先从哪些实验开始？

从 tour 根目录执行：

```sh
# 检查同步内容和本机工具；不下载、不访问开发板。
python3 tools/check_progress.py

# 直接用随附快照重放 19/20 的选定启动和故障检查。
python3 tools/verify_import.py

# 不依赖开发板、LiteX 或 PDK的内部扫描/RAM 故障实验。
python3 chapters/20a-dft-basics/run.py --output results/20a-tour-check

# 不依赖开发板的 CFU 原版 RTL 测试。
python3 chapters/13f-cfu-ml/run.py --direct-only --vectors 257 --seed 7
```

CFU 的独立测试固定写入 `results/13f-direct`；这条命令会更新该目录。若要保留原记录，运行前先备份。

ASIC 主线按顺序运行：

```sh
python3 chapters/18-ics55-spec/fetch_pdk.py
python3 chapters/19-asic-rtl/run.py --map-cells
python3 chapters/20-asic-verification/run.py
```

最后三条涉及 PDK 下载、交叉编译、综合和仿真，先按相应章节安装工具。19 的工艺 IO 模型需要较新的 Icarus；原实测使用 OSS CAD Suite 中的版本。tour 不依赖旁边 tutorial 的 external 目录；依赖应安装到自己的 external 或提供在 PATH 中。当前 LiteX 源码也可以通过 `LITEX_ROOT` 指定。

本次随附结果是 **tutorial 中已执行实验的快照**。本次在 tour 本地重新执行的检查另记在[同步验收](VALIDATION.md)，避免把复制证据写成新跑结果。

## 以后怎样同步？

```sh
python3 tools/sync_progress.py           # 预览
python3 tools/sync_progress.py --apply   # 同步 13–20A、公共说明、PLAN 和路径工具
python3 tools/sync_progress.py --check   # 比较当前源目录与导入文件
```

源目录默认是旁边的 tutorial，可用 `--source` 修改。工具不会删除 tour 文件，也不覆盖 00–12、首页、PLAN_zh。导入时自动排除教师资料和独立测验文件，并把正文中的课堂测验移除、概念问答改为实现说明。`--apply` 会覆盖范围内同名文件；本地改写前先保存自己的修改。

[sync-manifest.json](sync-manifest.json) 记录源 HEAD、源目录是否有未提交修改及导入文件的 SHA256。此次源目录包含未提交成果，因此只报 HEAD 不能完整定位内容，需结合文件哈希。

PLAN.md 是同步后的完整中文路线；首页已更新至 20A，PLAN_zh.md 仍是旧版计划。判断当前进度请以本页、PLAN.md 和对应结果为准。
