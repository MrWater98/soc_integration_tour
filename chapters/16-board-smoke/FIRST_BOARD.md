# 板子到货后的第一课：WSL 连接与开源 LED 实验

## 阅读说明与实际进展

本文件保留最初连接板子、修改 LED 的逐步操作。现在 Windows 已安装 usbipd，USB 已成功附加到 WSL，固定 LED 图案已下载并由用户确认；VexRiscv SoC 的 UART、按键与复位也已实测。完整运行逻辑先读 [本章 README](README.md)。

本地保留两个基础例子：`leds` 是固定输出，`clock` 是 27 MHz 计数闪灯，构建结果分别位于 `results/16-leds/leds.fs`、`results/16-clock/clock.fs`。下面的 BUSID 与设备路径都应以当前电脑实际枚举结果为准。

代码来自 [twied/TangPrimer-20K-example](https://github.com/twied/TangPrimer-20K-example)，固定提交 `7f26660abc25e1b79f6709bd00ca9cead8706494`，本章已复制两个例子的原始 RTL、约束和 WTFPL 许可。来源记录在 `examples/UPSTREAM.json`，不依赖外部仓库才能构建。

## 1. 先理解电脑怎样访问板子

```text
Windows 电脑
    |
    | 板卡 USB 已被 Windows 枚举
    v
usbipd-win：把选定的 USB 设备转交给 WSL
    |
    v
WSL 中的 openFPGALoader
    |
    | 与板上 USB-JTAG 下载器通信
    v
FPGA 自带的配置入口 --> 把 .fs 装入配置 SRAM --> LED 电路开始工作
```

WSL 的文件能访问 Windows，并不表示 WSL 自动拥有 USB 设备。我们要先建立 USB 转交，再执行 FPGA 下载。

这次用的 JTAG 是 FPGA 的配置入口，和 13A 自己写的教学 TAP 不同。LED 例子没有 CPU，也不需要 GDB/OpenOCD。

## 2. 接线

用能传数据的 Type-C 线，连接 Dock 标注的 **USB-JTAG/UART** 接口。对照官方照片，把 1 号拨码开关放到核心板使能位置；方向要跟照片对照。这里不用用户 USB 接口，也不用额外串口模块。[官方开箱说明](https://wiki.sipeed.com/hardware/zh/tang/tang-primer-20k/start.html)

## 3. 在 Windows 安装 USB 转交工具

保持 WSL 窗口打开，在 Windows PowerShell 执行：

```powershell
winget install --interactive --exact dorssel.usbipd-win
```

这是开源 USB/IP 工具，不是 FPGA 综合软件。安装驱动时，Windows 可能弹出管理员确认，需要用户在桌面操作。安装完成后重新打开 PowerShell：

```powershell
usbipd list
```

记下板卡对应那一行的 BUSID。确认方法是拔下板卡，再列一次；插回后新增的设备才是目标。BUSID 由系统分配，不能照抄其他人的 `4-4`。

**管理员 PowerShell** 中执行，替换 `实际BUSID`：

```powershell
usbipd bind --busid 实际BUSID
```

随后执行（attach 无需管理员）：

```powershell
usbipd attach --wsl --busid 实际BUSID
```

这组命令按 usbipd-win 5.x 的官方用法编写；如果安装了其他版本，先核对 `usbipd --version`。设备转交期间由 WSL 使用，Windows 端不能同时访问它。[Microsoft WSL USB 指南](https://learn.microsoft.com/en-us/windows/wsl/connect-usb)

## 4. 回到 WSL，先识别

在教程根目录执行：

```bash
lsusb
source chapters/15-fpga-build/tools.sh
openFPGALoader --version
openFPGALoader -b tangprimer20k --detect
```

第一条应出现板卡设备，最后一条才会尝试识别 JTAG 链上的 FPGA。我们期待本板核心型号 `GW2A-LV18PG256C8/I7` 对应器件，而不是只看“USB 已出现”。把检测输出交给助手核对后继续。

如果普通用户遇到 USB 权限错误，先查看实际设备节点权限、udev 服务及 openFPGALoader 规则；WSL 不一定已运行 udev。权限问题、设备未转交、FPGA 未使能是不同问题。[openFPGALoader 文档](https://trabucayre.github.io/openFPGALoader/)

## 5. 第一实验：固定 LED 图案

构建命令只生成文件，不访问板卡：

```bash
python chapters/16-board-smoke/build_examples.py --example leds
```

原始电路只有六个输出，值为 `6'b010011`。LED 是低有效：0 点亮，1 熄灭。按这个例子的 `nLed` 位编号，预期为：

| 位 | 5 | 4 | 3 | 2 | 1 | 0 |
| --- | --- | --- | --- | --- | --- | --- |
| 输出 | 0 | 1 | 0 | 0 | 1 | 1 |
| 灯 | 亮 | 灭 | 亮 | 亮 | 灭 | 灭 |
| FPGA 管脚 | L16 | L14 | N14 | N16 | A13 | C13 |

这是该例子的编号，和第 14 章 LiteX 的 LED 索引不是同一套顺序。上板时对照板上丝印确认。

识别成功后下载：

```bash
openFPGALoader -b tangprimer20k results/16-leds/leds.fs
```

该命令写 FPGA 配置 SRAM，没有 `-f` / `--write-flash`。下载后观察固定图案；断电后配置消失，重上电可能恢复出厂 Flash 中的程序。

这个实验成功，说明电脑→USB-JTAG→FPGA 配置→指定 LED 引脚这条路径能工作。

## 6. 第二实验：看见时钟在推进

```bash
python chapters/16-board-smoke/build_examples.py --example clock
openFPGALoader -b tangprimer20k results/16-clock/clock.fs
```

```text
板上 27 MHz 晶振 --> FPGA 的 H11 --> 计数器 --> 每次达到阈值就翻转六个 LED
```

初值为 `010101`，随后翻转成 `101010`，两组灯交替。源码参数 `ticks_per_second=27_000_000` 用来匹配当前板上参考时钟；不能把它当成每块板的固定值。代码从零计数、使用 `>= ticks_per_second/2`，翻转间隔实际为 13,500,001 个周期，接近半秒，完整亮灭周期接近一秒。这个例子不用 PLL。

固定图案成功但闪灯不工作时，我们就把排查范围缩到时钟引脚、时钟输入、计数逻辑和生成设计，而不重新怀疑所有 USB 操作。

## 7. 开源构建的三步在干什么？

```text
leds.v / clock.v
    |
Yosys：把 RTL 变成 FPGA 逻辑资源网表
    |
nextpnr-himbaechel：给这些资源安排位置、布线、检查时序
    |
Apicula / gowin_pack：把结果编码为 .fs
    |
openFPGALoader：通过板上下载器装入 FPGA
```

现有 OSS CAD Suite 已提供这四个工具，不需要 Gowin IDE，也不必为了这两个实验再搭 Docker。工具环境见第 15 章 `tools.sh`。

本地构建按当前核心板选择 `GW2A-LV18PG256C8/I7` 和 `GW2A-18C` 数据库，闪灯目标 27 MHz，并将 READY/DONE 复用脚启用为 GPIO；这两个复用脚正用于 LED。上游脚本使用 `GW2A-18`，还会构建后立即下载，所以本章使用可单独构建的脚本。完整命令、日志、资源、哈希和 RTL 快照保存在对应结果目录。

## 第一次完成后记录

记下实际 BUSID、`lsusb` 与 FPGA 检测输出、核心板/底板型号和版本，拍固定图案照片与闪灯短视频。构建通过、下载通过、实际灯光正确分别记录；只有完成实物观察才能把上板状态改成通过。
