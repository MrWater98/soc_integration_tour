"""Small cache-free LiteX/VexRiscv core for a bounded standard-cell RAM pilot."""
from migen import ClockDomain, ClockSignal, Instance, Module, ResetSignal, Signal
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc import SoCRegion
from litex.soc.interconnect import wishbone


class CRG(Module):
    def __init__(self, platform):
        self.clock_domains.cd_sys = ClockDomain("sys")
        self.comb += self.cd_sys.clk.eq(platform.request("clk"))
        self.specials += Instance("reset_sync", i_clk=self.cd_sys.clk,
            i_reset_n=platform.request("reset_n"), o_reset=self.cd_sys.rst)


class Registers(Module):
    def __init__(self, platform, gpio_width, uart_div):
        self.bus = b = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.irq = Signal()
        self.specials += Instance("peripheral", p_GPIO_WIDTH=gpio_width, p_UART_DIV=uart_div,
            i_clk=ClockSignal(), i_reset=ResetSignal(),
            i_cyc=b.cyc, i_stb=b.stb, i_we=b.we, i_sel=b.sel,
            i_adr=b.adr, i_dat_w=b.dat_w, o_dat_r=b.dat_r, o_ack=b.ack,
            i_gpio_in=platform.request("gpio_in"), o_gpio_out=platform.request("gpio_out"),
            o_uart_tx=platform.request("uart_tx"), o_irq=self.irq,
            o_result=platform.request("result"), o_stage=platform.request("stage"))
        self.comb += b.err.eq(0)


class TutorialSoC(SoCCore):
    def __init__(self, platform, rom_words, ram_size, gpio_width, uart_div):
        super().__init__(platform, clk_freq=1_000_000, bus_interconnect="crossbar",
            cpu_type="vexriscv", cpu_variant="minimal", cpu_reset_address=0,
            integrated_rom_size=4096, integrated_rom_init=rom_words,
            integrated_sram_size=256, integrated_main_ram_size=ram_size,
            with_uart=False, with_timer=False, with_ctrl=False, ident="")
        self.submodules.crg = CRG(platform)
        self.submodules.registers = Registers(platform, gpio_width, uart_div)
        self.bus.add_slave("registers", self.registers.bus,
            SoCRegion(origin=0x80000000, size=64, cached=False))
        self.comb += self.cpu.interrupt.eq(self.registers.irq)
