# 13C：OpenOCD 和适配器——命令怎样变成四根线？

## 先分清两件东西

**JTAG 适配器**通常是电脑与目标芯片之间的硬件：电脑送来命令，适配器产生引脚电平、采样 TDO，把结果送回电脑。

**OpenOCD**是运行在电脑上的软件。它知道如何通过适配器执行 JTAG 操作；配置了具体 CPU 目标后，还可以把调试请求转换为目标支持的操作。

```text
真实板卡：OpenOCD --> USB 驱动 --> 硬件适配器 --> TCK/TMS/TDI/TDO --> TAP
本章实验：OpenOCD --> TCP --> Python 模拟适配器 --> 仿真引脚 --> TAP RTL
```

这一章使用真实 OpenOCD，模拟的是适配器和目标电路。CPU 调试留到下一章先学软件操作；本章不用 GDB。

## 实验入口

依赖 Python、Icarus Verilog、OpenOCD。Ubuntu 可以安装：

```bash
sudo apt-get install openocd iverilog
python chapters/13c-openocd/run.py
```

脚本启动一个只监听本机的模拟适配器，自动分配空闲端口，生成 `results/13c/openocd.cfg`，然后启动 OpenOCD。不用插 USB，不访问真实板卡。

结果中：`openocd.log` 是软件读回；`remote-bitbang.txt` 是实际收到的适配器命令；`pins.csv` 是命令落到 RTL 后的逐事件引脚记录；`pins.html` 可拖动观察；`rtl/` 是完整编译输入。

本机验收使用 OpenOCD 0.10.0。配置采用该版本支持的 `interface`、`remote_bitbang_host/port`；新版本可能提示旧命令弃用。脚本设置 30 秒运行超时，支持本实验实际使用的 JTAG 命令，不实现 SWD 或完整适配器功能。

## 第一步：认识模拟适配器的命令

OpenOCD 的 remote_bitbang 驱动通过 socket 传递短命令。字符 `0` 到 `7` 表示 TCK、TMS、TDI 三个电平组成的二进制值，`R` 请求采样 TDO。[官方协议](https://github.com/openocd-org/openocd/blob/master/doc/manual/jtag/drivers/remote_bitbang.txt)

| 字符 | TCK | TMS | TDI | 动作 |
| --- | --- | --- | --- | --- |
| `2` | 0 | 1 | 0 | 在低时钟准备控制值 |
| `R` | 保持 | 保持 | 保持 | 把当前 TDO 回给 OpenOCD |
| `6` | 1 | 1 | 0 | 产生上升沿，TAP 推进一步 |

```text
OpenOCD 发 '2' --> Python 解码 010 --> SV 设置 tck=0,tms=1,tdi=0
OpenOCD 发 'R' --> Python 取 RTL 的 TDO --> 回一个字符 '0' 或 '1'
OpenOCD 发 '6' --> Python 解码 110 --> SV 产生 TCK 上升沿
```

这里 TCP 端口只是电脑上的连接参数，与芯片封装引脚无关。模拟时间随引脚命令推进，不模拟 USB 带宽或真实 JTAG 速率。

## 第二步：让 OpenOCD 找到 TAP

生成配置中的关键行：

```tcl
jtag newtap tutorial tap -irlen 4 -expected-id 0x12345679
init
scan_chain
```

`tutorial.tap` 是我们给这个目标取的名字。`-irlen 4` 要与 RTL 的 IR 长度相同；`-expected-id` 用来核对目标；运行器另从日志提取实际 ID 与期望比较，避免只看到工具继续运行就误判成功。OpenOCD 真正扫描引脚后，日志里出现 `0x12345679`。

可以用 `--expected-id 0x1234567b --output /tmp/13c-wrong-id` 故意设置错误期望，运行器应失败，日志会显示实际标识与期望的差异。这个选项改变的是测试软件的期望，不会改变当前 RTL 的教学 ID。

OpenOCD 可能根据这个教学 ID 的位字段打印厂商名称；那只是对字段的解释，不能据此把教学电路当成真实厂商芯片。

## 第三步：用一条命令代替几十拍

```tcl
irscan tutorial.tap 3
set first [drscan tutorial.tap 32 0x2468ace1]
set second [drscan tutorial.tap 32 0]
```

`irscan` 选择 USER，`drscan` 交换 32 位。OpenOCD 自动安排进入扫描、逐位传输、退出与提交。最终日志应当有：

```text
USER_OLD=CAFEF00D
USER_NEW=2468ACE1
```

这与 13A 的手写扫描同一行为，但本章实现和驱动代码都在本目录。第二次扫描提交全零，会把 USER 清零。

## 第四步：选错路径，再恢复

脚本再选 IR=4。本章 TAP 把这个未知编码转到单比特 BYPASS，送入全零后读回零，无法得到 IDCODE。随后选 IR=2，重新读回 `0x12345679`，日志记录 `WRONG_IR_DETECTED_AND_RECOVERED`。

因此排查读回错误时，可以同时看三层证据：

```text
软件：选了哪条 IR、要求读多少位？
适配器：实际收到哪些位操作、采样了几次？
RTL：TAP 是否进入 Shift、TDO 送出什么？
```

## 为什么此时还不能调试 CPU？

OpenOCD 已经能访问 TAP，但这个 TAP 只连接 IDCODE、USER、BYPASS，没有 CPU 调试模块。配置文件没有 `target create ...`，并关闭 GDB 服务。安装软件不会自动增加芯片里的停机、读寄存器和单步电路。

后面完整路径要是：

```text
GDB --> OpenOCD（认识目标 CPU）--> 适配器 --> 调试传输入口 --> 调试模块 --> CPU
```

下一章先让 GDB 调试一个本机递归程序，亲手理解“停下、看变量、看调用栈、继续”的含义，再讨论换成 SoC 时需要补什么。
