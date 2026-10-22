# 3. 一行一行读现成的CFU硬件

原文件是[upstream/cfu_mac.v](../upstream/cfu_mac.v)。本章复制自CFU Playground固定提交，没有改写核心。文件开头保留Apache许可，下面从module开始读。

## 3.1 module和端口

```verilog
module Cfu (
```

定义一个硬件模块，名字必须与LiteX包装器实例化的Cfu一致。它不会因为文件叫cfu_mac.v就自动改名。

```verilog
input cmd_valid,
output cmd_ready,
```

CPU表示“这里有一条命令”，CFU表示“我现在能接”。两者在上升沿同时为1，才接受一次命令。

```verilog
input [9:0] cmd_payload_function_id,
```

10位功能编号。本地CPU把指令的funct7七位和funct3三位拼在一起：`{funct7,funct3}`。不是10位RAM地址。

```verilog
input [31:0] cmd_payload_inputs_0,
input [31:0] cmd_payload_inputs_1,
```

两个32位操作数，通常来自CPU两个源寄存器。分别装四个输入字节和四个权重字节。

```verilog
output reg rsp_valid,
input rsp_ready,
output reg [31:0] rsp_payload_outputs_0,
```

CFU产生响应；CPU准备好接收时拉高rsp_ready。响应数据存在寄存器里，既作为当前结果输出，也作为下一次运算的累加器。

Verilog的reg表示由过程赋值的变量；是否真的形成触发器，还要看赋值位置。这里在posedge clk过程内赋值，因此形成状态存储。

```verilog
input reset,
input clk
);
```

reset高有效、同步采样；clk是与CPU相同的系统时钟。本模块没有生成自己的时钟。

## 3.2 固定输入偏移

```verilog
localparam InputOffset = $signed(9'd128);
```

localparam是编译时固定常量，不是CPU可写寄存器。9位有符号数能表示+128；如果错误地写成8位有符号128，会被解释成-128。`$signed`明确正负解释。

## 3.3 四路乘法

```verilog
wire signed [15:0] prod_0, prod_1, prod_2, prod_3;
```

声明四条16位有符号乘积连线。wire不是一个每拍保存结果的寄存器；这些表达式形成组合计算电路。

```verilog
assign prod_0 = ($signed(cmd_payload_inputs_0[7:0]) + InputOffset)
                * $signed(cmd_payload_inputs_1[7:0]);
```

依次理解：取lane0输入字节；解释为有符号数；加128；取lane0权重并解释为有符号数；相乘；把结果接到prod_0。

接下来的prod_1、prod_2、prod_3分别选择[15:8]、[23:16]、[31:24]，同一时间计算另外三对。不是一个乘法器被这个Verilog循环调用四次；源码中明确列出了四个组合乘法表达式，最后工具如何映射资源需看综合报告。

```verilog
wire signed [31:0] sum_prods;
assign sum_prods = prod_0 + prod_1 + prod_2 + prod_3;
```

将四个有符号乘积相加，得到32位组合结果。负值按有符号扩展参与运算，不是简单给高位补0。

## 3.4 接收条件

```verilog
assign cmd_ready = ~rsp_valid;
```

只要还有未交付响应，就不接受新命令。rsp_valid=0时cmd_ready=1；rsp_valid=1时cmd_ready=0。

这是单个结果槽位，不是深FIFO。响应交付的那拍也不同时接受下一条命令；最快情况下每两拍接受一条。本章不把“一拍内完成四路组合乘法”误写成“每拍都能启动一条新命令”。

## 3.5 时钟过程与优先级

```verilog
always @(posedge clk) begin
```

以下状态只在上升沿更新。

```verilog
if (reset) begin
    rsp_payload_outputs_0 <= 32'b0;
    rsp_valid <= 1'b0;
```

复位优先级最高：清累加器，丢弃任何待交付结果。`<=`是非阻塞赋值，本次沿先读取旧状态，再统一更新新状态；不是按源码顺序立刻改变寄存器。

```verilog
end else if (rsp_valid) begin
    rsp_valid <= ~rsp_ready;
```

已有响应时：CPU未准备好，rsp_ready=0，rsp_valid保持1；CPU准备好，rsp_ready=1，本拍消费响应，下拍valid变0。

这个分支没有给结果寄存器赋新值，所以结果保持。不应继续每拍累加同一组操作数，否则背压越久答案越大。

```verilog
end else if (cmd_valid) begin
    rsp_valid <= 1'b1;
```

只有没有待交付响应时才到这个分支。此时cmd_ready已为1，所以cmd_valid=1就代表一次命令被接受；运算后产生一个响应。

```verilog
rsp_payload_outputs_0 <= |cmd_payload_function_id[9:3]
    ? 32'b0
    : rsp_payload_outputs_0 + sum_prods;
```

这一行分五步看：

1. [9:3]就是funct7；低三位funct3在这个核心里不参与操作选择。
2. 前面的单个`|`是归约或：七位里有任意1，就得到1。
3. 得1：结果寄存器清零。
4. 得0：旧累加器加本次四路乘积和。
5. 更新后的值既保存为累加器，也作为该命令的返回值。

因此不是“funct7只有1才清零”：本核心把所有非零funct7都当清零。本章软件只使用1，避免给其他值发明不存在的功能。

最后几个end/endmodule结束条件、时钟过程和模块定义，不会再产生额外功能。

## 3.6 带数字走一遍时序

```text
沿到来之前       本次沿发生什么            沿之后
reset=1          清累加器                 result=0, valid=0, ready=1
clear命令有效    接受清零命令             result=0, valid=1, ready=0
CPU rsp_ready=1  消费响应                 result=0, valid=0, ready=1
MAC命令有效      接受输入并计算13         result=13,valid=1, ready=0
CPU rsp_ready=0  不消费                    result=13,valid=1, ready=0
CPU rsp_ready=0  继续等待                  result=13,valid=1, ready=0
CPU rsp_ready=1  消费                      result=13,valid=0, ready=1
```

CSV的accepted_cmd/accepted_rsp列记录**沿之前**的valid&ready；result_after记录沿之后的新结果。不要用沿之后已经变0的cmd_ready推断“刚才没有接受命令”。

## 3.7 最简单直通CFU与它有什么不同？

[cfu_passthrough.v](../upstream/cfu_passthrough.v)没有累加器：function_id最低位选择返回input0或input1，rsp_valid直接等于cmd_valid，cmd_ready直接等于rsp_ready。

它只有组合直通，所以不承诺撤销命令后还能保存响应。我们用单独的tb_passthrough检查这个接口，没有把乘加版“响应寄存保持”的测试错误套到直通版上。
