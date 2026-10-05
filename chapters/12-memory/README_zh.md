# 第 12 章：三种外部存储器，三种访问方法

前面的小 SoC 用片上 ROM 启动、片上 SRAM 放临时数据。容量变大时，外部存储器不能都当成“再接一块 SRAM”：异步 SRAM 要管片选和读写等待，SDRAM 要初始化与刷新，SPI Flash 则要用串行命令取数据。本章把三种实验放在独立子目录，均由真实 VexiiRiscv 程序发起访问。

## 先分清谁做什么

| 存储器 | 本章位置 | 上电/启动前 | CPU 怎样访问 | 本章证明什么 |
| --- | --- | --- | --- | --- |
| 片上 ROM | `0x00000000`，4 KiB | 固件镜像预置 | CPU 从这里取指 | 三个实验都从同一类启动 ROM 开始 |
| 片上 SRAM | `0x10000000`，4 KiB | 不依赖外部初始化 | CPU 普通 load/store | SDRAM 实验在初始化前把栈放这里 |
| 片上 main RAM | `0x40000000`，16 KiB；SRAM/Flash 两项使用 | 仿真初值不当作程序保证 | CPU 普通 load/store | 放 C 数据与栈 |
| 外部异步 SRAM | `0x90000000`，4 KiB | 无特殊初始化；内容不保证 | Wishbone 桥拆为 8 位并行引脚访问 | 读写等待、字节掩码、首末字 |
| LiteDRAM SDRAM | `0x40000000`，4 MiB；SDRAM 项替代片上 main RAM | **先执行 SDR 初始化序列** | LiteDRAM 控制器与 PHY 模型处理行/列、刷新 | 初始化、边界、数据模式、刷新后读回 |
| SPI Flash | `0xa0000000`，4 KiB 只读窗口 | `flash_image.hex` 预载模型 | 每个 CPU 读转为 `0x03`＋24 位地址＋32 位数据 | 镜像头、校验和、末字 |

三项实验使用**三个单独构建的 SoC**，地址 `0x40000000` 在 SDRAM 项代表外部 DRAM，在另两项代表片上 main RAM。每项的 `csr.csv` 才是该项实际地址图，不能把三张图混成一张。SRAM 和 Flash 被放在 VexiiRiscv 的 `0x80000000` 以上 IO 窗口，以便直接观察不经缓存的总线交易；它们不作为本章的取指区域。SDRAM 以 `main_ram` 接入，地图标记为 cached/rwx；本章只验证数据访问，没有验证从 SDRAM 执行代码。

## 为什么三个 SoC 的 `SoCCore` 参数不同？

三套构建都保留同一类 VexiiRiscv、复位地址 `0` 和 4 KiB 启动 ROM。可写内存则按固件需要配置：

| 构建 | `integrated_sram_size` | `integrated_main_ram_size` | LiteX 外部模块与敏感参数 |
| --- | ---: | ---: | --- |
| 异步 SRAM | 4 KiB | 16 KiB | `AsyncSRAM` 映射到 `0x90000000`，容量 4 KiB、不可缓存；`read_cycles=2`、`write_cycles=3` 控制字节通道的引脚等待。 |
| SDRAM | 4 KiB | 0 | `add_sdram(..., origin=0x40000000, size=4 MiB, l2_cache_size=0)` 自己建立 `main_ram`；SoC 时钟、LiteDRAM model 和 PHY 时钟都设为 50 MHz。 |
| SPI Flash | 4 KiB | 16 KiB | 只读桥映射到 `0xa0000000`，容量 4 KiB、不可缓存；每次 CPU load 都变成串行读取帧。 |

SDRAM 版本不要再把 4 MiB 填进 `integrated_main_ram_size`：`add_sdram` 已经创建了 `main_ram` 区域；4 KiB 集成 SRAM 则在 DRAM 初始化完成前供启动栈和运行时数据使用。改 SDRAM 几何却不改映射容量，会造成固件地址图与实际模型容量不一致。异步 SRAM 和 Flash 设 `cached=False`，让每次 CPU 读都能到达桥和器件模型；改成可缓存可能让协议检查看不到重复总线访问。修改起始地址或容量时，也要同步修改 linker region，并重新核对该构建生成的 `csr.csv`。

表格里反复出现的数值是本实验的配置，不是 SoC 的固定规则。例如，每个 4 KiB 区域都来自对应的 `SoCRegion` 和存储模型；ROM、片上 RAM 容量还要与链接脚本的 `MEMORY` 区域和固件镜像相符。SRAM/Flash 固件使用 16 KiB `main_ram`；SDRAM 构建则把 `integrated_main_ram_size` 设为 0，再把外部模型注册为 `main_ram`。只改其中一处，就会让生成的地址图、链接器假设或模型容量彼此不一致。

## 1. 异步 SRAM：32 位 CPU 怎样接 8 位芯片

`async-sram/soc.py` 使用 LiteX 的 `AsyncSRAM` Wishbone 桥，外部模型在 `async_sram_model.v`。CPU 一次 32 位写被桥拆成四次 8 位引脚写；`ce_n` 选中器件、`we_n` 为低时写，`oe_n` 为低时读。`read_cycles=2`、`write_cycles=3` 指每个字节阶段的等待设置，**整笔** Wishbone 字读写还包含四个通道和 ACK 周期，所以日志中的一次完整写可见 `wait=13`，读可见 `wait=9`。这些是当前配置的观测值。

固件依次做首字写读 `0x11223344`、只改字节通道 1 为 `0xaa`、末字 `0x55667788`、连续 8 字写读。检查 `ASRAM_ACK ... sel=2`：十六进制 `2` 即四个字节通道中的第 1 通道，首字读回应变为 `0x1122aa44`。模型还记录物理字节地址 `0x000` 和 `0xfff` 上的写入。首末地址都是**字节地址**；`ASRAM_ACK word=0x240003ff` 是 `0x90000ffc/4` 的 Wishbone 字地址。

## 2. SDRAM：先初始化，再相信读写

`sdram/soc.py` 使用 LiteDRAM 的 `LiteDRAMCore` 与 `SDRAMPHYModel`。教学几何为 4 个 bank、2048 行、256 列、16 位数据：`4 × 2048 × 256 × 2 = 4,194,304` 字节，即 4 MiB，范围 `0x40000000..0x403fffff`。系统时钟 50 MHz。几何缩小是为了让仿真能快速完成；时序参数沿用 `MT48LC4M16` 的 SDR 类型。`sdram/run.py` 记录实际 LiteDRAM 源码路径并核对 Builder 生成的容量。

这些几何和 50 MHz 都是当前仿真模型的参数。bank/row/column/数据宽度共同决定模型容量；`SDRAM_SIZE` 必须与容量、SoC 映射区域一致。改时钟时，也要让 SoC、PHY 模型和仿真时钟，以及生成的时序设置和按时钟计算的等待条件保持一致。这里的 4 MiB 是为了实验选的规模，不代表所有 SDRAM 芯片都只有这个容量。

启动代码把栈和 C 的 `.data/.bss` 放在**片上 SRAM**。固件随后使用 LiteDRAM 自动生成的 `sdram_phy.h` 执行 SDR 初始化命令序列，最后把 DFI 控制权交给硬件控制器。只有 `SDRAM_PROBE value=0x00000001` 出现后，程序才开始访问 DRAM。它检查首字、第二字、4 MiB 末字和 16 个连续模式值。延时跨越多次刷新后再次读回；这次运行的刷新计数从 `0xd3` 到 `0x1a1`。检查器要求**写入之后**至少又发生两次自动刷新，再接受最终成功码。计数值可变，因果顺序不变。

当前 Python 3.11 与 Migen 的 CSR 名称追踪不兼容；本章 `sdram/compat.py` 只在运行进程中补充 Python 3.11 字节码识别，避免修改 LiteX/LiteDRAM 源码。初始化和读写仍由实际 LiteDRAM 模型完成。

## 3. SPI Flash：读一个字也要发一帧命令

`spi-flash/run.py` 生成 4 KiB 模型内容：前 256 字节是镜像，头四字节为 ASCII `SOCF`，随后四字节是小端长度 `256`，第 252–255 字节是前 252 字节的字节求和校验，余下填 `0xff`。它同时保存二进制 `flash_image.bin`、文本字节 `flash_image.hex` 和 `image-check.txt`。这是一种教学镜像格式，不是通用 SPI Flash 文件格式。

4 KiB 映射窗口和 256 字节测试镜像是两个不同的长度：镜像只占窗口开头。24 位地址是桥当前 SPI 帧格式的一部分，`0x03` 是模型实现的读命令。改窗口或镜像大小时，要一起检查桥的地址切片、模型存储、固件边界/校验和及生成地址区域；改命令时要同步改桥与器件模型。

CPU 读 `0xa0000000` 时，`FlashReadBridge` 向独立的 `spi_flash_model.v` 发送 8 位读命令 `0x03`、24 位字节地址，再用 32 个时钟取四个数据字节；一笔完整读共 **64 位**。桥把 SPI 的先发字节顺序换成 CPU 小端 32 位字。固件检查 `SOCF`、长度、镜像校验和，以及 4 KiB 窗口末字是否是 `0xffffffff`。模型只支持读命令，本章没有擦除或编程行为。

运行器还会把镜像第 8 字节翻转 1 bit，再使用同一份固件和硬件重新仿真。头和长度仍正确，CPU 应在校验和处写出失败码 `0xe3`；记录保存在 `results/12-spi-flash/corrupt-image.log`。运行器随后恢复正常镜像。

## 运行与证据

LiteDRAM 是额外的外部库。可以安装它，或者在教程根目录准备固定源码版本并设置：

```sh
git clone https://github.com/enjoy-digital/litedram.git external/litedram
git -C external/litedram checkout 74522f715d7b10163ef6f6caa09887a90874be83
export LITEDRAM_ROOT="$PWD/external/litedram"
python3 chapters/12-memory/run.py
```

本机验收时使用的 LiteDRAM 提交为 `74522f715d7b10163ef6f6caa09887a90874be83`。LiteX 仍由教程根目录的 `tour_paths.py` 定位。若 LiteDRAM 已安装，`LITEDRAM_ROOT` 可不设置。也可单独执行三个子目录中的 `run.py`。

关键输出如下；每项完整日志、CSR 地图、编译记录和波形分别在 `results/12-async-sram/`、`results/12-sdram/`、`results/12-spi-flash/`：

```text
ASRAM_PROBE value=0x1122aa44
PASS 12-ASYNC-SRAM

SDRAM_PROBE value=0x00000001
SDRAM_REFRESH_COUNT before=0x000000d3 after=0x000001a1
PASS 12-SDRAM

FLASH_READ command=0x03 addr=0x000ffc bits=64
PASS 12-SPI-FLASH
PASS 12-MEMORY
```

预测：若把异步 SRAM 桥的 `read_cycles` 减小到不足模型稳定时间，谁可能先出错？若跳过 SDRAM 初始化，却直接把栈放进外部 main RAM，又会卡在什么阶段？请先指明 CPU、桥/控制器、外部模型各自负责哪一步，再看波形。

## 常见问题

### LiteX 的 AsyncSRAM 和 `async_sram_model.v` 各负责什么？

AsyncSRAM 是总线桥：接收 Wishbone 请求，驱动 `ce_n/we_n/oe_n/address/data` 等芯片侧信号，并在读写完成后应答 CPU。Verilog 模型是桥另一侧的存储器：按这些引脚保存和返回字节。只有桥没有外部器件行为，读数就没有来源；只有模型没有 SoC 总线桥，CPU 也无法按地址访问它。

### SDRAM 能像 SRAM 一样复位后直接读写吗？

不能。SDRAM 上电后需要按器件要求初始化，之后控制器还要周期刷新。本实验先把栈和运行时放在片上 SRAM，再执行 LiteDRAM 生成的初始化序列，确认初始化完成后才访问外部 DRAM。读写通过只证明数据路径；初始化和写入后刷新计数也要单独检查。

### 这些模型能证明真实芯片时序吗？

不能。它们证明 CPU、桥/控制器和数字模型之间的功能交互。真实 FPGA 还要确认引脚约束、时钟和时序收敛；ASIC 还要使用目标宏模型并检查宏时序。行为模型不会自动覆盖板级延迟、模拟特性或器件所有 datasheet 角落。

### 为什么三个外存实验不能共用一张地址图？

每个实验单独构造一套 SoC。相同的 CPU 地址在 SDRAM 配置里连到外部 DRAM，在另外两套里可能连到片上 main RAM。各自 Builder 生成的 `csr.csv` 才是该次构建的实际地图；把这些地图拼在一起会让同一地址看起来同时属于不同存储器。

## 本章速记

1. 外部异步 SRAM 的 Wishbone ACK 要等并行引脚事务完成，字节掩码决定哪些芯片字节被写。
2. SDRAM 在初始化之前不能作为可靠的 C 栈；初始化后由控制器负责自动刷新。
3. 内存映射 SPI Flash 的 CPU 读会变成串行 `0x03` 读帧；本章窗口只读。
4. 地址地图、模型协议日志与 CPU 读回分别证明配置、传输和软件结果。
