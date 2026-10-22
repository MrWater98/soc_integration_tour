# 17C Linux 输入检查

上游版本：4781064597af671037ca1712a212a61022f1b26c。

实际尝试：

```bash
PYTHONPATH=/home/ziyue/researchlib/Micro_Eletronic/litex \
python external/linux-on-litex-vexriscv/make.py \
  --board sipeed_tang_primer_20k --toolchain apicula \
  --cpu-count 1 --rootfs mmcblk0p2
```

状态：生成未通过，未构建 bitstream、未启动 Linux。

当前环境的 litex-boards 为 2023.12，目标中使用隐式 `ClockDomain()` 名称，在 Python 3.11 失败；该目标还固定 `toolchain="gowin"`，需要明确改为 Apicula。使用默认已安装 LiteX 时，还遇到新 LiteEth 导入 Agilex PLL 与旧 LiteX 的版本不匹配；设置源码 LiteX 的 PYTHONPATH 后通过了该导入，接着遇到上述时钟域命名错误。

已安装 VexRiscv-SMP 数据包与 LiteSDCard。后续应固定相互兼容的 LiteX/Migen/LiteX-Boards/LiteDRAM/LiteEth/LiteSDCard 版本，使用独立目标适配，再验证 DDR 与开源布局布线。当前板上稳定性测试仍采用单核普通 VexRiscv 与片内 RAM。
