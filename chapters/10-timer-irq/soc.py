"""Minimal VexRiscv SoC with LiteX Timer and a visible external IRQ line."""
from migen import Display, Finish, If, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage
from litex.soc.interconnect.csr_eventmanager import EventManager, EventSourceProcess

COMPLETION_BASE = 0x80000000


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        request = bus.cyc & bus.stb
        self.isr_write = Signal()
        self.comb += self.isr_write.eq(request & bus.we & (bus.adr == COMPLETION_BASE // 4 + 1))
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(request & ~bus.ack & bus.we,
            If(bus.adr == COMPLETION_BASE // 4,
                Display("TIMER_POLL packed=0x%08x", bus.dat_w),
            ),
            If(bus.adr == COMPLETION_BASE // 4 + 1,
                Display("TIMER_ISR packed=0x%08x", bus.dat_w),
            ),
            If(bus.adr == (COMPLETION_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w), Finish(),
            ),
        )


class ProjectTimer(Module, AutoCSR):
    """LiteX Timer countdown/events with explicit CSR names for this Python build."""
    def __init__(self):
        self._load = CSRStorage(32, name="load")
        self._reload = CSRStorage(32, name="reload")
        self._en = CSRStorage(1, name="en")
        self._update_value = CSRStorage(1, name="update_value")
        self._value = CSRStatus(32, name="value")
        self.submodules.ev = EventManager()
        self.ev.zero = EventSourceProcess(edge="rising")
        self.ev.finalize()
        count = Signal(32)
        self.count = count
        self.sync += [
            If(self._en.storage,
                If(count == 0, count.eq(self._reload.storage)).Else(count.eq(count - 1))
            ).Else(count.eq(self._load.storage)),
            If(self._update_value.wr_stb, self._value.status.eq(count)),
        ]
        self.comb += self.ev.zero.trigger.eq(count == 0)


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words, reset_mode=None):
        super().__init__(platform,
            clk_freq=1_000_000, cpu_type="vexriscv", cpu_variant="minimal", bus_arbiter="transaction",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=16*1024, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 10")
        self.add_module("timer0", ProjectTimer())
        self.irq.add("timer0", use_loc_if_exists=True)
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETION_BASE, size=0x1000, mode="rw", cached=False))
        irq_was_high = Signal()
        self.sync += [irq_was_high.eq(self.cpu.interrupt[0]),
            If(self.cpu.interrupt[0] & ~irq_was_high,
                Display("IRQ_LINE_ASSERT source=timer0")),
            If(~self.cpu.interrupt[0] & irq_was_high,
                Display("IRQ_LINE_CLEAR source=timer0")),
        ]
        self.test_reset = Signal()
        if reset_mode is not None:
            if reset_mode == "count":
                trigger = self.timer0._en.storage & (self.timer0.count > 0) & (self.timer0.count < 600)
            elif reset_mode == "isr":
                trigger = self.completion.isr_write
            else:
                raise ValueError(f"未知复位时机: {reset_mode}")
            state = Signal(2)
            delay = Signal(4)
            self.sync.por += If(state == 0,
                If(trigger,
                    self.test_reset.eq(1), state.eq(1), delay.eq(7),
                    Display(f"TIMER_RESET_ASSERT mode={reset_mode}"),
                ),
            ).Elif(state == 1,
                If(delay == 0,
                    self.test_reset.eq(0), state.eq(2),
                    Display(f"TIMER_RESET_RELEASE mode={reset_mode}"),
                ).Else(delay.eq(delay - 1)),
            )
