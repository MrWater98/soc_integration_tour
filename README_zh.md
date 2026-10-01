# SoC 集成实践

这是一个可复现、逐步推进的 SoC 集成项目，使用 LiteX 和单核 VexiiRiscv。前七步从工具链和 Wishbone 验证开始，依次完成 ROM 启动、SRAM、地址译码，最后迁移到 LiteX `SoCCore` 与 `Builder`。

每一步都有独立实现和运行命令。日志、固件镜像、地址图和波形写入 `results/`，不纳入 Git。

| 步骤 | 集成结果 | 运行命令 |
| --- | --- | --- |
| 00 环境 | 固定 LiteX/VexiiRiscv 版本，检查主机仿真工具 | `python3 chapters/00-environment/check_env.py --strict --wishbone --soc` |
| 01 CPU | 原生 VexiiRiscv 复位、ROM 取指、store 与无 ACK 场景 | `PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py` |
| 02 Wishbone | 独立验证从设备事务和应答故障 | `python3 chapters/02-wishbone/verify.py` |
| 03 ROM | 固件镜像、复位映射和执行完成标志 | `PYTHONHASHSEED=0 python3 chapters/03-rom/run.py` |
| 04 SRAM | 可写存储器、字节通道、栈和越界故障 | `PYTHONHASHSEED=0 python3 chapters/04-sram/run.py` |
| 05 地址图 | ROM/SRAM/寄存器译码、重叠和未映射访问 | `PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py` |
| 06 LiteX SoC | `SoCCore`/`Builder` 集成和地址图校验 | `PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py` |

完整范围和后续集成阶段见 [PLAN.md](PLAN.md)。
