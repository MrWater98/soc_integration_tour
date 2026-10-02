"""CPU-visible bit-bang pins with independent SPI/I2C protocol responders."""
from pathlib import Path
from migen import Cat, ClockSignal, ResetSignal, Display, Finish, If, Instance, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

COMPLETION_BASE = 0x80000000


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        request = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(request & ~bus.ack & bus.we,
            If(bus.adr == COMPLETION_BASE // 4,
                Display("PROTOCOL_PROBE value=0x%08x", bus.dat_w),
            ),
            If(bus.adr == (COMPLETION_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w), Finish(),
            ),
        )


class SPIDevice(Module):
    """Mode-0, MSB-first 8-bit command followed by 8-bit reply."""
    def __init__(self, clk, cs_n, mosi, miso):
        old_clk = Signal()
        old_cs = Signal(reset=1)
        bits = Signal(5)
        command = Signal(8)
        reply = Signal(8, reset=0xa5)
        self.comb += If(~cs_n & (bits >= 8) & (command == 0x9f),
            miso.eq(reply[7])).Else(miso.eq(1))
        self.sync += [old_clk.eq(clk), old_cs.eq(cs_n),
            If(cs_n,
                If(~old_cs,
                    If(bits == 16, Display("SPI_FRAME command=0x%02x bits=%d", command, bits)),
                ),
                bits.eq(0), command.eq(0), reply.eq(0xa5),
            ).Else(
                If(clk & ~old_clk,
                    bits.eq(bits + 1),
                    If(bits < 8, command.eq((command << 1) | mosi)),
                ),
                If(~clk & old_clk & (bits > 8), reply.eq(Cat(0, reply[:7]))),
            ),
        ]


class ProjectSPI(Module, AutoCSR):
    def __init__(self):
        # bit 0=CLK, bit 1=MOSI, bit 2=CS_N; reset leaves slave unselected.
        self.out = CSRStorage(3, reset=4, name="out")
        self.input = CSRStatus(1, name="input")
        clk, mosi, cs_n, miso = Signal(), Signal(), Signal(), Signal()
        self.comb += [clk.eq(self.out.storage[0]), mosi.eq(self.out.storage[1]),
                      cs_n.eq(self.out.storage[2]), self.input.status.eq(miso)]
        self.submodules.device = SPIDevice(clk, cs_n, mosi, miso)


class ProjectI2C(Module, AutoCSR):
    def __init__(self, platform):
        # Released=1, pulled low=0. Device may only pull SDA low; the pull-up makes idle=1.
        self.out = CSRStorage(2, reset=3, name="out")
        self.input = CSRStatus(2, name="input")
        scl, sda = Signal(), Signal()
        device_release = Signal(reset=1)
        self.comb += [scl.eq(self.out.storage[1]),
                      sda.eq(self.out.storage[0] & device_release),
                      self.input.status.eq(Cat(sda, scl))]
        platform.add_source(str(Path(__file__).with_name("i2c_device.v")))
        self.specials += Instance("i2c_device",
            i_clk=ClockSignal(), i_rst=ResetSignal(), i_scl=scl, i_sda=sda,
            o_release_sda=device_release)


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words):
        super().__init__(platform,
            clk_freq=1_000_000, cpu_type="vexiiriscv", cpu_variant="standard",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=16*1024, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 11")
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETION_BASE, size=0x1000, mode="rw", cached=False))
        self.add_module("spi", ProjectSPI())
        self.add_module("i2c", ProjectI2C(platform))
