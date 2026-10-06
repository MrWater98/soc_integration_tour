"""A read-only memory window backed by a real 0x03 SPI read transaction."""
from pathlib import Path
from migen import C, Cat, ClockSignal, Display, Finish, FSM, If, Instance, Module, NextState, NextValue, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

FLASH_BASE = 0xa0000000
COMPLETE_BASE = 0x80000000


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        active = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(active & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(active & ~bus.ack & bus.we,
            If(bus.adr == COMPLETE_BASE // 4,
                Display("FLASH_PROBE value=0x%08x", bus.dat_w)),
            If(bus.adr == (COMPLETE_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w), Finish()),
        )


class FlashReadBridge(Module):
    """For each Wishbone word read, send 0x03 + 24-bit address + 32 clocks."""
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.cs_n = Signal(reset=1)
        self.sclk = Signal()
        self.mosi = Signal()
        self.miso = Signal(reset=1)
        tx = Signal(32)
        rx = Signal(32)
        bit_number = Signal(6)
        self.comb += [self.mosi.eq(tx[31]),
            bus.dat_r.eq(Cat(rx[24:32], rx[16:24], rx[8:16], rx[0:8])),
            bus.err.eq(0)]
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(bus.cyc & bus.stb & ~bus.we,
                NextValue(tx, Cat(C(0, 2), bus.adr[:10], C(0, 12), C(3, 8))),
                NextValue(rx, 0), NextValue(bit_number, 0),
                NextValue(self.cs_n, 0), NextValue(self.sclk, 0),
                NextState("LOW")),
        )
        fsm.act("LOW", NextState("RISE"))
        fsm.act("RISE", NextValue(self.sclk, 1), NextState("SAMPLE"))
        fsm.act("SAMPLE",
            If(bit_number >= 32, NextValue(rx, Cat(self.miso, rx[:31]))),
            NextState("FALL"))
        fsm.act("FALL",
            NextValue(self.sclk, 0),
            NextValue(tx, Cat(C(0, 1), tx[:31])),
            If(bit_number == 63, NextState("ACK")).Else(
                NextValue(bit_number, bit_number + 1), NextState("LOW")),
        )
        fsm.act("ACK", bus.ack.eq(1),
            Display("FLASH_WB_READ word=0x%08x raw=0x%08x", bus.adr, rx),
            NextValue(self.cs_n, 1), NextState("IDLE"))


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words):
        super().__init__(platform,
            clk_freq=1_000_000, cpu_type="vexriscv", cpu_variant="minimal", bus_arbiter="transaction",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=16*1024, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 12 SPI Flash")
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETE_BASE, size=0x1000, mode="rw", cached=False))
        self.add_module("flash", FlashReadBridge())
        self.bus.add_slave(name="flash", slave=self.flash.bus,
            region=SoCRegion(origin=FLASH_BASE, size=0x1000, mode="r", cached=False))
        platform.add_source(str(Path(__file__).with_name("spi_flash_model.v")))
        self.specials += Instance("spi_flash_model", i_clk=ClockSignal(),
            i_cs_n=self.flash.cs_n, i_sclk=self.flash.sclk,
            i_mosi=self.flash.mosi, o_miso=self.flash.miso)
