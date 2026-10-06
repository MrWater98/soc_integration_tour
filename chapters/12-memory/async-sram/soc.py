"""LiteX AsyncSRAM bridge to an independent byte-wide external SRAM model."""
from pathlib import Path
from migen import ClockSignal, Display, Finish, If, Instance, Module, Signal
from litex.soc.cores.ram.async_sram import AsyncSRAM
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

EXT_BASE = 0x90000000
COMPLETE_BASE = 0x80000000


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        active = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(active & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(active & ~bus.ack & bus.we,
            If(bus.adr == COMPLETE_BASE // 4,
                Display("ASRAM_PROBE value=0x%08x", bus.dat_w)),
            If(bus.adr == (COMPLETE_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w), Finish()),
        )


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words):
        super().__init__(platform,
            clk_freq=1_000_000, cpu_type="vexriscv", cpu_variant="minimal", bus_arbiter="transaction",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=16*1024, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 12 Async SRAM")
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETE_BASE, size=0x1000, mode="rw", cached=False))

        pads = platform.request("ext_sram")
        self.add_module("ext_sram", AsyncSRAM(pads, read_cycles=2, write_cycles=3))
        self.bus.add_slave(name="ext_sram", slave=self.ext_sram.bus,
            region=SoCRegion(origin=EXT_BASE, size=0x1000, mode="rw", cached=False))
        platform.add_source(str(Path(__file__).with_name("async_sram_model.v")))
        self.specials += Instance("async_sram_model",
            i_clk=ClockSignal(), i_ce_n=pads.ce_n, i_oe_n=pads.oe_n,
            i_we_n=pads.we_n, i_adr=pads.adr, io_dat=pads.dat)

        wait_count = Signal(6)
        bus = self.ext_sram.bus
        self.sync += If(bus.cyc & bus.stb,
            If(bus.ack,
                Display("ASRAM_ACK word=0x%08x we=%d sel=%x wait=%d", bus.adr,
                        bus.we, bus.sel, wait_count),
                wait_count.eq(0),
            ).Else(wait_count.eq(wait_count + 1)),
        ).Else(wait_count.eq(0))
