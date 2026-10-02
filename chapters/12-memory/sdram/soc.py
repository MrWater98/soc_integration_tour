"""LiteDRAM controller with an SDR SDRAMPHYModel and a small teaching geometry."""
from migen import Display, Finish, If, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore
from litedram.modules import MT48LC4M16
from litedram.phy.model import SDRAMPHYModel

SYS_CLK_HZ = 50_000_000
SDRAM_BASE = 0x40000000
SDRAM_SIZE = 4 * 1024 * 1024
COMPLETE_BASE = 0x80000000


class SmallSDRAMModel(MT48LC4M16):
    """Same SDR timings as MT48LC4M16; reduced geometry for a fast simulation."""
    nrows = 2048
    ncols = 256


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.refresh_count = Signal(32)
        refresh_before = Signal(32)
        active = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(active & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(active & ~bus.ack & bus.we,
            If(bus.adr == COMPLETE_BASE // 4,
                Display("SDRAM_PROBE value=0x%08x", bus.dat_w),
                If(bus.dat_w == 2, refresh_before.eq(self.refresh_count)),
                If(bus.dat_w == 3,
                    Display("SDRAM_REFRESH_COUNT before=0x%08x after=0x%08x",
                            refresh_before, self.refresh_count))),
            If(bus.adr == (COMPLETE_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w), Finish()),
        )


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words):
        super().__init__(platform,
            clk_freq=SYS_CLK_HZ, cpu_type="vexiiriscv", cpu_variant="standard",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=0, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 12 LiteDRAM")
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETE_BASE, size=0x1000, mode="rw", cached=False))

        module = SmallSDRAMModel(SYS_CLK_HZ, "1:1")
        self.submodules.ddrphy = SDRAMPHYModel(module, data_width=16, clk_freq=SYS_CLK_HZ)
        self.add_sdram("sdram", phy=self.ddrphy, module=module,
            origin=SDRAM_BASE, size=SDRAM_SIZE, l2_cache_size=0)
        refresh = self.sdram.controller.refresher.cmd
        refresh_count = Signal(32)
        self.comb += self.completion.refresh_count.eq(refresh_count)
        self.sync += If(refresh.valid & refresh.ready & refresh.ras & refresh.cas & ~refresh.we,
                        refresh_count.eq(refresh_count + 1))
