"""A real LiteX CPU/CFU system; the CFU RTL itself is unmodified upstream code."""
from pathlib import Path
from migen import Display, Finish, If, Module, Signal
from litex.soc.integration.soc_core import SoCCore
from litex.soc.integration.soc import SoCRegion
from litex.soc.interconnect import wishbone

BASE = 0x80000000


class TraceEndpoint(Module):
    def __init__(self, commands, responses):
        self.bus = b = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.comb += [b.ack.eq(b.cyc & b.stb), b.err.eq(0), b.dat_r.eq(commands)]
        self.sync += If(b.cyc & b.stb & b.we,
            If(b.adr==BASE//4+1, Display("CFU_DOT result=%0d",b.dat_w)),
            If(b.adr==BASE//4+2, Display("CFU_DENSE_0 result=%0d",b.dat_w)),
            If(b.adr==BASE//4+3, Display("CFU_DENSE_1 result=%0d",b.dat_w)),
            If(b.adr==BASE//4+4, Display("CFU_CPU_REFERENCE_CYCLES value=%0d",b.dat_w)),
            If(b.adr==BASE//4+5, Display("CFU_ACCEL_CYCLES value=%0d",b.dat_w)),
            If(b.adr==BASE//4+6, Display("CFU_RANDOM_CHECKS count=%0d",b.dat_w)),
            If(b.adr==BASE//4+8, Display("CFU_PREPACKED_CYCLES value=%0d",b.dat_w)),
            If(b.adr==BASE//4+7,
                If(b.dat_w==0x5a,
                    Display("CFU_COMPLETE code=0x%08x commands=%0d responses=%0d",b.dat_w,commands,responses)
                ).Else(Display("CFU_FAIL code=0x%08x commands=%0d responses=%0d",b.dat_w,commands,responses)),
                Finish()))


class TutorialSoC(SoCCore):
    def __init__(self, platform, *, rom_words):
        super().__init__(platform,clk_freq=1_000_000,
            cpu_type="vexriscv",cpu_variant="full+cfu",cpu_reset_address=0,
            cpu_cfu=str(Path(__file__).with_name("upstream")/"cfu_mac.v"),
            integrated_rom_size=4096,integrated_rom_init=rom_words,
            integrated_sram_size=4096,integrated_main_ram_size=16384,
            with_uart=False,with_timer=False,with_ctrl=False,ident="CFU tutorial")
        self.commands=Signal(32)
        self.responses=Signal(32)
        b=self.cpu.cfu_bus
        self.sync += [If(b.cmd.valid & b.cmd.ready,self.commands.eq(self.commands+1)),
                      If(b.rsp.valid & b.rsp.ready,self.responses.eq(self.responses+1))]
        self.add_module("trace",TraceEndpoint(self.commands,self.responses))
        self.bus.add_slave("trace",self.trace.bus,
            SoCRegion(origin=BASE,size=64,cached=False))
