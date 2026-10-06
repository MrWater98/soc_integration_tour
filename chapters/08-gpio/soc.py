"""Chapter 08: LiteX SoC with GPIO CSR inputs and outputs."""
from migen import Display, Finish, If, Module, Mux, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage
from migen.genlib.cdc import MultiReg

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


class GPIOInput(Module, AutoCSR):
    """Small explicit-name equivalent of LiteX GPIOIn, for robust name extraction."""
    def __init__(self, pads):
        self._input = CSRStatus(len(pads), name="input")
        self.specials += MultiReg(pads, self._input.status)


class GPIOOutput(Module, AutoCSR):
    """Small explicit-name equivalent of LiteX GPIOOut."""
    def __init__(self, pads):
        self.output = CSRStorage(len(pads), reset=0, name="output")
        self.comb += pads.eq(self.output.storage)


class ProjectSoC(SoCCore):
    """This chapter's ROM, RAM, completion endpoint, and GPIO banks."""
    def __init__(self, platform, *, rom_words):
        super().__init__(
            platform,
            clk_freq=1_000_000,
            cpu_type="vexriscv",
            cpu_variant="minimal", bus_arbiter="transaction",
            cpu_reset_address=0x00000000,
            integrated_rom_size=0x1000,
            integrated_rom_init=rom_words,
            integrated_sram_size=0x1000,
            integrated_main_ram_size=16 * 1024,
            with_uart=False,
            with_timer=False,
            with_ctrl=False,
            ident="SoC Integration Tour Chapter 08",
        )
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(
            name="completion",
            slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETION_BASE, size=0x1000, mode="rw", cached=False),
        )
        gpio_in_pads = platform.request("gpio_in")
        gpio_out_pads = platform.request("gpio_out")
        self.add_module("gpio_in", GPIOInput(gpio_in_pads))
        self.add_module("gpio_out", GPIOOutput(gpio_out_pads))

        # Change the external input after reset, as if a button/switch moved.
        stimulus = Signal(4)
        counter = Signal(11)
        self.sync += If(counter < 1000, counter.eq(counter + 1))
        self.comb += [stimulus.eq(Mux(counter < 1000, 0, 5)), gpio_in_pads.eq(stimulus)]
        self.sync += If(counter == 999, Display("GPIO_INPUT_DRIVE value=0x5"))
        # GPIOIn synchronizes external pins; this monitor reports the actual output pads.
        out_value = Signal(4)
        old_value = Signal(4, reset=0xF)
        self.comb += out_value.eq(gpio_out_pads)
        self.sync += [old_value.eq(out_value), If(out_value != old_value,
            Display("GPIO_OUTPUT value=0x%x", out_value))]
