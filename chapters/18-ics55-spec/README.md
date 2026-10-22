# 18：把 RTL 接到真正的 ICS55 标准单元库

FPGA 综合把逻辑映射到 LUT、触发器和 BRAM。ASIC 综合要把逻辑映射到工艺库里的门和触发器。这一章先用一个 16 位计数器走通库接入，再整理 SoC 首版规格。

```text
counter.v：加一、复位
       │ Yosys synth / dfflibmap / abc
       ▼
标准单元网表：DFFQX1H7R、INVX0P5H7R、AND...
       ├─ Verilog 单元模型 → Icarus → 复位、计数、回绕是否正确
       ├─ Liberty → OpenSTA → 单元延迟与建立/保持检查
       └─ LEF / CDL → 核对网表使用的单元是否有对应视图
```

## 每一种库文件回答什么问题？

| 视图 | 用途 |
|---|---|
| Liberty `.lib` | 门的逻辑、延迟、时序约束、面积等；综合和 STA 使用 |
| Verilog | 标准单元的行为；门级仿真使用 |
| LEF | 单元尺寸、引脚与布线障碍；布局布线使用 |
| GDS | 实际版图几何；最终版图合并使用 |
| CDL | 晶体管连接；LVS 核对使用 |

有这些文件不等于芯片可以提交流片。还要走布局、供电网络、时钟树、寄生提取、物理时序、DRC/LVS，并确认 IO、存储宏、封装与制造方接收条件。

## 可复现的小实验

```bash
python chapters/18-ics55-spec/fetch_pdk.py
python chapters/18-ics55-spec/run.py
```

PDK 固定为官方 `v1.10.102`，提交 `ebc3f7e5d22a67f9423e0d980cd056291a58f307`。只下载本次 RVT 小实验需要的 Liberty 与 GDS 压缩包，记录大小和 SHA256。库放在 `external/`，不用把整个 PDK 提交进教程。

Yosys 与 Icarus 使用现有开源工具链；OpenSTA 若不在 PATH，脚本使用 `external/opensta/usr/bin/sta`。本次实际工具为 OpenSTA 2.0.17，来自 Ubuntu 的 opensta 包。新环境需要先安装这些工具，例如 Ubuntu 上的 `sudo apt install opensta iverilog`；Yosys 也可使用前面配置好的 OSS CAD Suite。当前机器的系统包管理器存在其他包配置问题，因此我用 `apt-get download opensta` 下载包，再用 `dpkg-deb -x` 解包到 `external/opensta`，没有覆盖系统工具。

本次使用 `typ_tt_1p2_25`：典型工艺、1.2 V、25°C。该条件来自所选库文件；不是宣称芯片只有一个供电值或只能在 25°C 工作。20 ns 时钟周期也是实验输入，可以通过 `--period-ns` 修改，最终芯片频率必须覆盖目标工艺、电压、温度角及实际布线。

`run.py` 完成四个实际检查：

1. 映射到 ICS55 单元，不能停留在 Yosys 的通用门。
2. 检查使用的单元在 LEF/CDL 中存在。
3. 用工艺库 Verilog 模型仿真 70,000 个周期，检查复位、计数和 16 位回绕。
4. 用 OpenSTA 读真实 Liberty 和映射网表，输出建立与保持路径。

这里门级仿真启用 `functional`，没有 SDF 回标。STA 使用理想时钟，没有布局后的线网寄生。结果保存到 `results/18`，完整 RTL 与单元模型放在 `rtl/`；具体状态见 `summary.json`。

## 为什么先做计数器？

如果直接放整个 CPU，失败可能来自 CPU 网表、存储器、工艺库、综合脚本或时钟约束。计数器只需要组合门与触发器，却已经能检查标准单元映射、时钟、复位和各视图衔接。走通这一步后，才能逐项引入 ROM、RAM、IO 与 SoC。

## 规格现在能冻结吗？

先形成 [SPEC.md](SPEC.md) 中的候选规格。SRAM 宏、IO 电压与 ESD、封装引脚、制造接收规则还未确定，这些直接决定面积、时钟、存储容量和顶层接口，因此当前状态是候选，尚未冻结。

[官方 PDK](https://github.com/openecos-projects/icsprout55-pdk) 的公开内容与 [文档](https://icsproutpdk.openecos.com/zh-cn/latest/) 是输入来源。FPGA 的 rPLL 和 BRAM 不能原样搬到 ASIC；外部时钟可作为首版候选，SRAM 则需取得实际宏，或为小容量寄存器实现重新评估面积。

另外用 `--period-ns 0.1` 故意设置无法满足的周期，OpenSTA 报告违例，脚本返回失败。这样也验证了脚本不会只因为工具正常退出就把时序标成通过。
