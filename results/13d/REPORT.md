# 13D GDB 入门

PASS：断点进入 fact(3)、fact(2)、fact(1)，观察调用栈，finish 返回 fact(2)、fact(3)，结果为 6。

目标架构：x86_64-linux-gnu。这是宿主进程调试；未连接 SoC。

|停下位置|SP 相对 fact(3) 的变化（字节）|
|---|---|
|fact(3)|0|
|fact(2)|-48|
|fact(1)|-96|
|返回 fact(2)|-48|
|返回 fact(3)|0|
