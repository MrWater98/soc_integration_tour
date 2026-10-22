# 14.4：跟着一次按钮操作，把代码与电路串起来

本篇是一条完整的阅读路线。使用默认 Tang 27 MHz 结果；不需要重新下载或改动板子。

## 场景一：启动后，为什么能看到 HELLO？

```text
FPGA 被配置
  ↓ 配置写入逻辑、寄存器初值、ROM 内容
por 计数器从 65536 开始递减
  ↓ 清零，且按钮0松开
PLL 退出复位并锁定
  ↓ 系统复位同步释放
VexRiscv 复位入口为 0
  ↓ 取 ROM[0]
_start 设置 sp → 初始化数据区 → call main
  ↓
main 关闭 UART 事件，写 LED，调用 text
  ↓
text 从 ROM 读取字符串，逐字符写 UART FIFO
  ↓ UART 发出串行位
Dock USB 桥把它转成电脑可读的串口数据
```

这条路径里，Python 的作用已经在生成阶段完成。CPU 根据 ROM 指令执行 C 程序；PLL、UART 状态机、GPIO 连接同时作为电路持续工作。

## 场景二：按按钮1，LED5 怎样亮？

按下前，外部 `btn_n1=1`；按下后变为 0。硬件先取反，所以内部输入变为 1。

1. 在 [tang_soc.py](../../tang_soc.py) 找 `ButtonInput(~platform.request('btn_n',1))`。
2. 在 [io_cores.py](../../io_cores.py) 的 `ButtonInput` 找 `MultiReg` 和 `CSRStatus`。
3. 在生成的 `csr.h` 找 `buttons_input_read()`，确认它访问 `CSR_BASE+0x1000`。
4. 在 [main_tang.c](../../main_tang.c) 找按钮轮询和 `leds_output_write(buttons & LED_MASK)`。
5. 在同一头文件找 LED 写地址 `CSR_BASE+0x800`。
6. 在生成顶层找 LED CSR 存储更新，再找 `assign led5` 的反相连接。
7. 在 CST 找 `led5` 对应 C13。

最后的效果：

```text
外部 btn_n1=0
   ↓ 反相、同步
buttons_input_read() 返回 1
   ↓ C 程序 mask=1
leds_output_write(1)
   ↓ CSRStorage 保存 1
led5=~1=0
   ↓ C13 上输出低电平
LED5 亮
```

松开过程反向变化。CSR 读写需要 CPU 执行和总线事务，因此 LED5 的响应晚于引脚本身的变化；两级输入同步和软件轮询也带来延迟。

## 场景三：CPU 卡住，两个灯会怎样？

若 CPU 卡在 `character()` 等待发送 FIFO，LED4 的独立心跳仍可能继续，LED5 则保持上一次存储值。因为 CSRStorage 不会因 CPU 暂停执行就自动消失。

```text
LED4 在闪：心跳时钟/复位/计数器这条路径仍在工作
没有 ALIVE：需检查 CPU、程序、总线、UART 等路径
LED5 不跟按钮：需检查按钮输入、CSR 地址、CPU 轮询与 LED 输出
```

一个观察只能证明它对应的路径。把两条 LED 与串口结合，才更容易定位问题。

## 场景四：为什么写 54 MHz 后，不能只换串口设置？

系统时钟影响 CPU、UART 分频、心跳计数等。正确操作是改生成参数并使用新的结果目录：

```bash
python chapters/14-fpga-platform/tang_run.py \
  --sys-clk-hz 54000000 --output results/14-tang20k-54mhz
```

新的 `manifest.json` 应写系统时钟 54000000，`soc.h` 应有对应配置，RTL 的 rPLL 参数也应改变。UART 波特率仍可保持 115200，因为电路重新根据新系统时钟计算它。

这一步还没有完成时序检查或下载。继续使用新结果进行第 15 章构建；不能拿默认 27 MHz 顶层和 54 MHz 初值/约束混成一套输入。

## 用命令对照当前文件

从仓库根目录执行这些只读命令：

```bash
# 身份、时钟、容量、PLL
python -m json.tool results/14-tang20k/manifest.json

# 软件函数和硬件地址
rg -n 'CSR_BASE|LEDS_OUTPUT_ADDR|BUTTONS_INPUT_ADDR|leds_output_write|buttons_input_read' \
  results/14-tang20k/builder/software/include/generated/csr.h

# CPU 与时钟实际在顶层的连接
rg -n 'VexRiscv|rPLL|assign led|readmemh' \
  results/14-tang20k/rtl/tutorial14.v

# C 调用最后编译成了什么
riscv64-unknown-elf-objdump -d results/14-tang20k/firmware/program.elf
```

如果构建目录/ELF 尚不存在，先运行 `tang_run.py`。文件访问失败不能直接解释为芯片电路缺失；要先区分哪些产物已保存、哪些需在本地重新生成。

## 修改什么，需要重新做哪一步？

| 修改对象 | 受影响的步骤 |
| --- | --- |
| C 的输出字符串、按钮处理 | 编译固件 → 更新 ROM → 重新生成 RTL/初值 → FPGA 构建/下载 |
| CSR 名称、外设数量、地址图 | 重新生成头文件 → 重编 C → 重新生成电路 → 构建/下载 |
| 心跳频率、系统时钟、RAM 容量 | 重新生成硬件和相关固件参数 → 构建/检查时序 → 下载 |
| 球位、IO 标准 | 核对板卡连线 → 更新平台/约束与审核表 → 重新构建/下载 |
| 只改 README | 不改变 FPGA 电路或程序 |

最值得记住的对应关系是：**Python 描述连接，地址图连接软件与寄存器，C 编译成指令，ROM 保存指令，CST 把顶层信号连接到板子。**
