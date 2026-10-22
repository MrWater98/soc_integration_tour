# 17b-delayed：SMP 双核 RTL 仿真

完整实现解释见 [对应章节 README](../../chapters/17b-smp-dual/README.md)。本文件说明这个结果目录的用途；它不会重跑实验或改变已有统计。

## 文件怎样产生？

本章 Python 先生成 CSR 接口，GCC 编译本章 startup.S/main.c，第二遍生成同配置电路与 ROM 初值。`rtl/` 是集群核心、缓存 RAM、顶层、内存模型、所有初值和测试台的完整快照；`sources.json` 保存哈希。Verilator/C++ 编译宿主仿真器，测试台按 UART TX 位流重建文字，主机核对 hart 结果、原子数、IRQ 与复位次数。

`run.log` 是实际仿真输出，`summary.json` 是本章检查器的结论，`commands.json` 保存编译命令。`firmware/`、`obj/` 等未全部提交；需要时执行对应章节入口。

- `status`：PASS: real SMP RTL and independent mailbox checks
- `harts`：2
- `work_per_hart`：257
- `reset_runs`：3
- `fault_stop`：False
- `fault_mailbox`：False
- `delay_hart_loop_iterations`：3000
- `fpga`：NOT_RUN

仿真不是板卡实测；故障目录的 PASS 指准确捕获预期错误，并不表示故障程序正常完成。
