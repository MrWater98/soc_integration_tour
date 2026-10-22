# 本次同步验收（2026-10-22）

## 内容与文件完整性

- 导入 1841 个文件，约 104 MB；包括 13–20A 的章节源码、图示、完整 RTL 输入和 Git 规则保留的实验记录。
- 62 个导入 Python 文件通过语法检查；新增工具也通过语法检查。
- 检查结果目录中 171 处字面量 `$readmemh/$readmemb` 引用，初始化文件均存在。
- 同步文件 SHA256 与导入清单一致；章节/公共说明中的相对 Markdown 链接已检查。
- 原 00–12 章、README.md、README_zh.md、PLAN_zh.md 没有修改。PLAN.md 采用当前 tutorial 的路线，按 tour 的已有章节名调整链接，并注明 00–12 尚未逐项重新验收。

机器检查记录见 [check.json](check.json)，来源与每文件哈希见 [sync-manifest.json](sync-manifest.json)。

## 在 tour 路径重新执行

### CFU 独立 RTL

```sh
python3 chapters/13f-cfu-ml/run.py --direct-only --vectors 257 --seed 7
```

261 组向量（4 固定 + 257 随机）、8 个直通检查、0–7 周期背压、复位恢复、错误偏移负例均通过。新执行的摘要和日志保存在 [validation/cfu](validation/cfu/summary.json)。

脚本会覆盖固定的 `results/13f-direct`。为了保留本次导入的历史快照，保存新运行证据后已通过同步工具恢复原快照。本次没有重跑真实 CPU 的 CFU 全流程；619 次命令等结果来自导入记录。

### 内部扫描与 RAM March

```sh
python3 chapters/20a-dft-basics/run.py --output results/20a-tour-check
```

扫描列举故障 8 个，正常功能检测 2 个，扫描检测 8 个；RAM 列举故障 19 个，全部检测。每个扫描案例退出测试并复位后，正常运行恢复检查通过。新摘要见 [validation/dft](validation/dft/summary.json)。

### 第 19、20 章的本地快照重放

```sh
python3 tools/verify_import.py
```

工具从本地 `results/19/rtl` 编译，分别启动 RTL、通用网表和 ICS55 工艺网表；再执行 20 章两次启动、无 ACK 和错误 GPIO 的选定用例。编译产物写临时目录，日志和摘要写 [validation/replay](validation/replay/summary.json)。使用随快照保留的标准单元模型，不要求重新下载 PDK。

**本次六个检查均通过**：RTL、通用网表、ICS55 网表启动；两次复位启动；缺失 ACK 的 watchdog 检出；错误 GPIO 的固件失败码检出。工艺模型编译时有 Icarus 不支持部分 timing checks 的警告，本次按功能模型运行，没有验证单元延迟或建立/保持时间。

这组重放检查不重新生成硬件、不重新综合，也不执行完整 20 章覆盖/形式/随机回归。具体本次执行结果以该目录 summary.json 为准。

## 当前环境与剩余工作

当前 PATH 有 Icarus、Verilator、Yosys、RISC-V GCC、OpenOCD、GDB。tour 自己的 external 下尚未安装 OSS CAD Suite、OpenSTA 或 ICS55 PDK；nextpnr、Apicula 和下载器在此环境的普通 PATH 中也不可用。重建 FPGA、重新工艺映射时应按章节准备依赖。

本次没有连接开发板、重新下载 FPGA、执行 FPGA 布局布线或 ASIC 物理设计。导入的板上记录和静态时序结果保留原测量范围。
