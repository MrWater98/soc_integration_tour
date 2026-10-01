# 01 — VexiiRiscv 复位与首次写入

## 集成变更

实例化 LiteX 原生 `vexiiriscv/standard` CPU，连接 64 字节初始化 ROM 和字节地址 `0x40` 的内存映射写端点。程序执行 `addi x1,x0,64`，再执行 `sw x1,0(x1)`。

```text
VexiiRiscv AXI-Lite pBus（字节地址）
                │
                ▼  LiteX 原生 AXILite2Wishbone
       32 位 Wishbone（字地址）
          ├── ROM       0x00000000–0x0000003f
          └── 写端点    0x00000040–0x0000007f
```

LiteX 在注册 CPU 主设备时创建总线适配器。本阶段只配置 CPU 和 Wishbone 端点，不实现适配器。

## 运行与验收

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

原生 CPU 仿真运行两次。正常场景必须记录复位地址 `0x0` 的取指以及向字节地址 `0x40` 写入 `0x40`。负例保持 ACK 为低，必须观察到写请求等待，不能误报正常写完成。tiny bus 是独立的端点时序检查，不能替代 CPU 仿真。

生成证据位于 `results/01/` 和 `results/01-no-ack/`，包括构建/编译/运行日志、地址图和 VCD 波形。

## 接口约束

- CPU 侧地址是字节地址；32 位字寻址的 Wishbone 端点看到 `0x40 / 4 = 0x10`。
- Wishbone 请求在 `cyc`、`stb` 同时为高时有效；只有目标设备给出 ACK 才算完成。
- 预取可能产生多次 ROM 读取。取指标记表示观察到总线请求；端点写入证明固件执行到了 store。

阶段 02 使用可控测试主设备单独验收从设备应答行为。
