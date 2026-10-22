# Tang 150 MHz 实验：目标时序失败

RTL/固件生成与 Yosys 综合通过。nextpnr seed=1 写出 routed.json 和 pnr-report.json，但 CPU 目标 150 MHz 未满足，最终 Fmax 估计为 117.47 MHz。

初步放置报告的 99.43 MHz 不是最终结果；最终以路由后报告为准。构建已停止，没有使用 timing-allow-fail，没有打包 .fs、下载板子、改变种子重试或生成图片。

原始证据在 nextpnr.log、commands.json、pnr-report.json。Fmax 是这份实现的工具估计，不是器件的最高规格。
