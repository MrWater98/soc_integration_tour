"""A VexRiscv SoC with LiteX UART and a pin-level serial loopback."""
from migen import Cat, Display, Finish, If, Module, Signal
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

SYS_CLK_HZ = 1_000_000
BAUD = 100_000
BIT_CYCLES = SYS_CLK_HZ // BAUD
COMPLETION_BASE = 0x80000000


class CompletionSlave(Module):
    def __init__(self):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        request = bus.cyc & bus.stb
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
        self.sync += If(request & ~bus.ack & bus.we,
            If(bus.adr == COMPLETION_BASE // 4,
                Display("UART_RX_BYTE value=0x%02x", bus.dat_w),
            ),
            If(bus.adr == COMPLETION_BASE // 4 + 1,
                Display("UART_FIFO_FULL seen=0x%08x", bus.dat_w),
            ),
            If(bus.adr == (COMPLETION_BASE + 0xffc) // 4,
                Display("SOC_COMPLETE data=0x%08x", bus.dat_w),
                Finish(),
            ),
        )


class SerialLoopback(Module):
    """Wire TX to RX and independently sample each 8N1 frame at bit centers."""
    def __init__(self, pads, *, decode_cycles):
        self.comb += pads.rx.eq(pads.tx)
        prev_tx = Signal(reset=1)
        state = Signal(2)  # 0: idle, 1: data, 2: stop
        cycles = Signal(max=decode_cycles * 2)
        bit_number = Signal(3)
        received = Signal(8)
        self.sync += prev_tx.eq(pads.tx)
        self.sync += If(state == 0,
            If(prev_tx & ~pads.tx,
                state.eq(1), cycles.eq(decode_cycles + decode_cycles//2 - 1),
                bit_number.eq(0), received.eq(0),
            ),
        ).Elif(cycles != 0,
            cycles.eq(cycles - 1),
        ).Elif(state == 1,
            received.eq(Cat(received[1:], pads.tx)),
            cycles.eq(decode_cycles - 1),
            If(bit_number == 7, state.eq(2)).Else(bit_number.eq(bit_number + 1)),
        ).Else(
            If(pads.tx,
                Display("UART_TX_BYTE value=0x%02x", received),
            ).Else(
                Display("UART_FRAME_ERROR"),
            ),
            state.eq(0),
        )


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, rom_words, monitor_bit_cycles=BIT_CYCLES,
                 reset_during_tx=False):
        super().__init__(platform,
            clk_freq=SYS_CLK_HZ, cpu_type="vexriscv", cpu_variant="minimal", bus_arbiter="transaction",
            cpu_reset_address=0, integrated_rom_size=0x1000,
            integrated_rom_init=rom_words, integrated_sram_size=0x1000,
            integrated_main_ram_size=16*1024, with_uart=False, with_timer=False,
            with_ctrl=False, ident="SoC Integration Tour Chapter 09")
        self.add_module("completion", CompletionSlave())
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=COMPLETION_BASE, size=0x1000, mode="rw", cached=False))
        pads = platform.request("serial")
        self.add_uart(name="uart", uart_name="serial", uart_pads=pads,
            baudrate=BAUD, fifo_depth=4, rx_fifo_rx_we=True)
        self.add_module("serial_loopback", SerialLoopback(pads, decode_cycles=monitor_bit_cycles))
        self.test_reset = Signal()
        if reset_during_tx:
            # The por domain keeps running while the sys domain is reset.
            prev_tx = Signal(reset=1)
            state = Signal(2)
            delay = Signal(4)
            self.sync.por += [prev_tx.eq(pads.tx),
                If(state == 0,
                    If(prev_tx & ~pads.tx, state.eq(1), delay.eq(3),
                       Display("UART_RESET_TRIGGER: TX start bit")),
                ).Elif(state == 1,
                    If(delay == 0,
                        self.test_reset.eq(1), state.eq(2), delay.eq(7),
                        Display("UART_RESET_ASSERT: frame incomplete"),
                    ).Else(delay.eq(delay - 1)),
                ).Elif(state == 2,
                    If(delay == 0,
                        self.test_reset.eq(0), state.eq(3),
                        Display("UART_RESET_RELEASE"),
                    ).Else(delay.eq(delay - 1)),
                ),
            ]
