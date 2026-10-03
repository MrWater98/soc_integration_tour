# 03 —— 从汇编到真正启动的 ROM 镜像

第 01 章按地址从一小段内联指令返回数据。本章改为用 RISC-V 工具链编译固件、打包完整的初始化 ROM，并让同一颗 VexiiRiscv 从复位地址 0 启动。

## 汇编怎样变成 ROM 内容？

```text
program.S
   │ riscv64-unknown-elf-gcc（rv32im、ilp32，链接地址 0）
   ▼
program.elf ── objcopy -O binary ──> program.bin（字节）
                                      │ 每 4 字节按小端序组合
                                      ▼
                                 program.hex（32 位字）
                                      │ 用 NOP 补足到 256 字
                                      ▼
                                 rom_init.hex（完整 1 KiB 镜像）
                                      │ integrated_rom_init
                                      ▼
                           LiteX ROM → VexiiRiscv 取指
```

代码链接到 `0x0`，因为 CPU 复位地址为 `0x0`，ROM 也从这里开始。`rv32im` 选择指令集，`ilp32` 选择 32 位 ABI。编译器构建的是软件，不是 CPU RTL。

## LiteX 在这里负责哪一段？

`ProjectSoC` 仍继承 `SoCCore`：CPU、Wishbone 主总线、CSR 和 ROM 总线从 LiteX 来；本章把编译得到的 `words` 传给 `integrated_rom_init`，并把 ROM 容量设为 `len(words) * 4`。因此镜像长度、ROM 容量、复位地址、链接地址是一个整体：256 个字对应 1024 字节，复位 PC 为 0，固件也链接在 0。改变其中一个时，其余几项和生成地图都要重新核对。

完成端点则是项目自己写的 Wishbone 从设备。`self.add_module(...)` 注册 Migen 模块，`self.bus.add_slave(...)` 把接口接入主总线，`SoCRegion` 声明 `0x20000000–0x20000fff` 地址范围；`SoCIORegion` 登记 CPU 的 I/O 区域。`cached=False` 标记它是有副作用的 MMIO 端点，不应按普通内存处理。`Builder(..., compile_software=False)` 只构建 gateware/仿真工程，软件编译由本章的 `cpu_sim.py` 单独控制，便于先检查 ELF、二进制镜像和边界条件。

## 常见问题

### 为什么需要好几个镜像文件？

`program.elf` 保存可执行段和调试符号。`program.bin` 是从 ELF 提取出来的连续字节。`program.hex` 把这些字节按每行一个 32 位字写出，便于 Python 检查和打包。`rom_init.hex` 固定为 256 个字，也就是 `256 × 4 = 1024` 字节；未使用部分填 NOP。SHA-256 文件用于确认生成文件身份。

### 小端序的打包是什么意思？

最低有效字节放在最低地址。假设四个字节依次为 `b7 02 00 20`，组成的 32 位指令字就是 `0x200002b7`。辅助脚本按小端序每四字节合成一个字，再把字拆回字节并比较，确保打包没有把字节顺序弄反。

### memory map 描述什么？

它约定 CPU 可见的字节地址由哪个硬件区域响应。地址表本身不会自动生成译码逻辑；LiteX 的 bus/region 或项目中的译码器必须实现这份约定。

| 区域 | 字节地址范围 | 用途 |
| --- | --- | --- |
| ROM | `0x00000000–0x000003ff` | 复位代码和固件，1 KiB |
| 完成端点 | `0x20000000–0x20000fff` | 仿真寄存器，记录固件写入的 `0x35` |
| CSR | `0xf0000000–0xf000ffff` | LiteX 控制/状态寄存器空间 |

软件地址图使用字节地址；这里的 32 位 Wishbone 按字寻址，所以字节地址 `0x20000000` 对应 Wishbone 字地址 `0x08000000`。比较固件、生成地图和总线波形时要把单位写清楚。

### 怎样知道 CPU 真的执行了程序？

运行脚本先检查 ROM 镜像非空且不超过 256 字，并检查复位地址对齐且位于 ROM 内；随后核对生成地址图。仿真时还必须看到 CPU 从地址 0 取指，最后由完成端点收到 `0x35` 并应答。完成写入是运行证据；镜像构建成功或地址表生成成功只证明配置和构造。

### 为什么测试容量边界和错误配置？

257 字的镜像放不进 256 字 ROM；复位地址 `0x1000` 在 ROM 末尾之外；复位地址 1 又没有按指令对齐。这些错误都应在 CPU 仿真前被拒绝，避免最后只看到难以解释的取指失败。

## 运行与观察

```sh
PYTHONHASHSEED=0 python3 chapters/03-rom/run.py
```

检查 `results/03/` 下的 `program.elf`、`program.bin`、`program.hex`、`rom_init.hex`、哈希、`memory_map.csv`、`run.log` 和 VCD。固件向完成端点写 `0x35`，端点收到该值后才打印 `SOC_COMPLETE`。从 0 取指说明 CPU 进入 ROM；完成标志说明固件执行到了测试检查点。

## PASS 能证明什么？

通过表示汇编生成的镜像放得进配置的 ROM，复位地址和地址图检查一致，且 VexiiRiscv 执行到了预期完成写入。第 04 章再加入可写 SRAM，并检查字节通道和栈访问。
