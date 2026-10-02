"""Chapter 07: LiteX SoC with main RAM for bare-metal C."""
from migen import Display, Finish, If, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

COMPLETION_BASE = 0x80000000
COMPLETION_CODE = 0x5A


class CompletionSlave(Module):
    """Simulation-only memory-mapped endpoint used to end the CPU test."""
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.value = Signal(32)
        request = bus.cyc & bus.stb
        last_word = (COMPLETION_BASE + 0xFFC) // 4
        self.comb += [bus.dat_r.eq(self.value), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(request & ~bus.ack & bus.we,
            self.value.eq(bus.dat_w),
            If(bus.adr == COMPLETION_BASE // 4,
                Display("SOC_PROBE data=0x%08x", bus.dat_w),
            ),
            If(bus.adr == last_word,
                If(bus.dat_w == COMPLETION_CODE,
                    Display("SOC_COMPLETE word_address=0x%08x data=0x%08x sel=%x", bus.adr, bus.dat_w, bus.sel),
                ).Else(
                    Display("SOC_FAIL word_address=0x%08x data=0x%08x sel=%x", bus.adr, bus.dat_w, bus.sel),
                ),
                Finish(),
            ),
        )


class ProjectSoC(SoCCore):
    """This chapter's ROM, SRAM, main RAM, and completion endpoint."""
    def __init__(self, platform, *, rom_words, integrated_main_ram_size,
                 main_ram_init):
        super().__init__(
            platform,
            clk_freq=1_000_000,
            cpu_type="vexiiriscv",
            cpu_variant="standard",
            cpu_reset_address=0x00000000,
            integrated_rom_size=0x1000,
            integrated_rom_init=rom_words,
            integrated_sram_size=0x1000,
            integrated_main_ram_size=integrated_main_ram_size,
            integrated_main_ram_init=main_ram_init,
            with_uart=False,
            with_timer=False,
            with_ctrl=False,
            ident="SoC Integration Tour Chapter 07",
        )
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(
            name="completion",
            slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETION_BASE, size=0x1000, mode="rw", cached=False),
        )
