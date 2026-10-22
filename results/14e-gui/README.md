# 14E：用 nextpnr GUI 查看 Gowin 布线快照

## 已完成什么？

- WSLg 显示环境已确认，修复版 GUI 已成功加载并显示窗口。
- 读取 150.49 MHz（heap 时序权重 20、seed 3）的原始快照，实际恢复到 nextpnr 上下文后再次导出。
- 逐项比较 **7293 个单元的 BEL 位置、8082 条非空网络的路由、58372 个资源三元组**，全部一致。
- 原 OSS CAD Suite 和 14E 时序实验保留；本轮未重新布局布线、打包或下载板子。

## 为什么原工具报 array2d 越界？

错误出现在 JSON 读取后的 `attributesToArchInfo()`，恢复 BEL 时调用 Gowin 后端的 `notifyBelChange()`。后者使用 `fast_logic_cell` 布局缓存；这个缓存仅在 `prePlace()` 初始化。直接恢复已布线快照时未经过该阶段，缓存宽度为 0，于是触发：

```text
Assertion failure: x >= 0 && x < m_width
common/kernel/array2d.h:78
```

查看补丁在缓存尚未初始化时跳过这个仅维护布局缓存的回调；通用层仍完成 BEL / wire / PIP 绑定。查看 GUI 时不用重新运行 placer。该独立版本用于浏览，频率结果引用原工具已有报告。

还有两个加载细节：RTL 顶层叫 tutorial14，路由 JSON 顶层叫 top；查看入口自动读模块名。独立编译的程序需要显式指定芯片数据库，本入口使用原 SDK 的 GW2A-18C 数据库。

## 构建来自哪里？

源码固定为 `861c57be9c9a0c38ab60b0eabd19903db37efa22`，与原 SDK 的提交一致。除了恢复流程的保护，还补充两个 Qt5 CMake 分支，使用当前系统的 Qt5。补丁见 [nextpnr-readonly-gui.patch](../../chapters/14e-seed-sweep/patches/nextpnr-readonly-gui.patch)。

编译目录在 external/nextpnr-gui-viewer/build，原程序在 external/fpga-tools/oss-cad-suite，两者独立。查看入口默认选择前者。构建需要 Git、Ninja、C++ 编译器、Boost、Python 开发文件与 Qt5 开发文件；当前环境已有这些库。脚本将 CMake 和 Eigen 依赖放在 external/nextpnr-viewer-deps，未替换系统库。

CMake 使用现有芯片数据库，因此不重新生成 Gowin 数据库；空的 HIMBAECHEL_GOWIN_DEVICES 列表用于跳过数据库生成目标。实际器件仍由 GUI 命令的 --device 和 --chipdb 指定。

## 怎么使用？

在 tutorial 根目录执行：

```bash
# 首次构建；本机已经完成，可直接运行下面的查看命令
python chapters/14e-seed-sweep/build_gui_viewer.py
python chapters/14e-seed-sweep/view_gui.py

# 查看旧默认参数 seed 2 的快照
python chapters/14e-seed-sweep/view_gui.py --input results/14e/best/routed.json.gz

# 重放实际上下文恢复检查
python chapters/14e-seed-sweep/verify_gui_restore.py
```

查看快照时直接浏览；重新实现新设计继续使用原来的章节构建和 14E 算法实验入口。

## 这些文件为什么产生？

| 文件 | 产生方式 | 用途 |
| --- | --- | --- |
| build-manifest.json | build_gui_viewer.py | 源码提交、补丁/可执行文件哈希、实际配置命令 |
| configure.log | CMake | 编译器和依赖发现、生成构建规则 |
| build.log | Ninja | 查看程序的编译过程 |
| restore.log | verify_gui_restore.py 调用实际工具 | 真实 JSON 恢复和导出的执行记录 |
| restore-summary.json | 比较原始和重新导出的上下文 | 位置、路由完整一致的验收证据 |
| window-tree.txt | WSLg 下 xwininfo | GUI 窗口已映射的记录 |

恢复检查规范化空 ROUTING 属性：空串/空格代表无路由，不将这些条目算作线路。原始快照 SHA256 为 `c76ba62500f8bcb4882e383bd342ba69c64919cab9d13e6621e8beed6ab460ac`。数字对应这份快照，不是 FPGA 固有的资源数量。

GUI 的缩放、搜索、网络高亮与 nextpnr 工作流程见 [第 14 章](../../chapters/14-fpga-platform/README.md#用-nextpnr-gui-交互查看布局布线)。


## GUI 为什么显得杂乱？怎样改进？

原界面显示底层资源框架，许多单元用同一种白色表示；控制台占用较多屏幕。Gowin 原 drawBel 还缺少块 RAM、DSP、PLL、IO 的绘图分支。科学绘图则筛选已用单元、分类着色并汇总线路密度，两者呈现的信息层次不同。

查看版本增加浅色配色、资源分类图例与常用资源符号，默认关闭 wire/PIP/group 细节，默认浏览 Cells，控制台可通过 Console 开关显示。修正浅背景颜色的浮点归一化，并按窗口宽高比适配视图。位置与连接来自同一份已验证快照。

![改进后的交互视图](gui-after.png)

[改进前的截图](gui-before.png)。资源符号是位于真实坐标上的示意标记，大小不代表宏面积或存储容量。样式修改同样保存在查看补丁中；新频率实验继续使用原 SDK。
