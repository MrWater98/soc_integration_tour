"""Chapter-local VexiiRiscv SoC: native AXI-Lite CPU and Wishbone project endpoints."""
from migen import Display, Finish, If, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCIORegion, SoCRegion
from litex.soc.integration.soc_core import SoCCore

COMPLETE_BASE = 0x20000000


class RegisterSlave(Module):
    def __init__(self, *, expected, finish_at_first=False):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.value = Signal(32)
        request = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(self.value), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(request & ~bus.ack & bus.we,
            If(bus.adr == COMPLETE_BASE // 4,
                self.value.eq(bus.dat_w),
                Display("REGISTER_WRITE data=0x%08x", bus.dat_w),
                *([If(bus.dat_w == expected,
                    Display("SOC_COMPLETE data=0x%08x", bus.dat_w),
                ).Else(Display("SOC_FAIL data=0x%08x", bus.dat_w)), Finish()]
                  if finish_at_first else []),
            ),
            If(bus.adr == (COMPLETE_BASE + 0xffc) // 4,
                If(bus.dat_w == expected,
                    Display("SOC_COMPLETE data=0x%08x", bus.dat_w),
                ).Else(Display("SOC_FAIL data=0x%08x", bus.dat_w)),
                Finish(),
            ),
        )
        self.sync += If(request & ~bus.ack & ~bus.we & (bus.adr == COMPLETE_BASE // 4),
            Display("REGISTER_READ data=0x%08x", bus.dat_r))


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words, sram_size=0, expected=0x5a,
                 finish_at_first=False):
        super().__init__(platform, clk_freq=1_000_000,
            cpu_type="vexiiriscv", cpu_variant="standard", cpu_reset_address=0,
            integrated_rom_size=len(rom_words) * 4, integrated_rom_init=rom_words,
            integrated_sram_size=0, integrated_main_ram_size=0,
            with_uart=False, with_timer=False, with_ctrl=False)
        if sram_size:
            self.add_module("onchip_sram", wishbone.SRAM(sram_size))
            self.bus.add_slave(name="onchip_sram", slave=self.onchip_sram.bus,
                region=SoCRegion(origin=0x10000, size=sram_size, mode="rw", cached=True))
        self.bus.add_region("endpoint_io", SoCIORegion(origin=COMPLETE_BASE, size=0x1000))
        self.add_module("registers", RegisterSlave(expected=expected, finish_at_first=finish_at_first))
        self.bus.add_slave(name="registers", slave=self.registers.bus,
            region=SoCRegion(origin=COMPLETE_BASE, size=0x1000, mode="rw", cached=False))
        rom_bus = self.rom.bus
        first_fetch = Signal()
        self.sync += If(rom_bus.cyc & rom_bus.stb & rom_bus.ack & ~first_fetch,
            first_fetch.eq(1), Display("FETCH first_word_address=0x%08x", rom_bus.adr))
