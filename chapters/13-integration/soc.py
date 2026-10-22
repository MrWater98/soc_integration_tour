"""Chapter 13: one SoC, real UART/IRQ paths, and independent protocol models.

GPIO/Timer use explicit-name adaptations of LiteX's BSD-licensed cores.
SPI/I2C and serial monitoring are local tutorial simulation models.
"""
from pathlib import Path
from migen import Cat, ClockSignal, ResetSignal, Display, Finish, If, Instance, Module, Mux, Record, Signal
from migen.genlib.cdc import MultiReg
from litex.soc.interconnect import wishbone
from litex.soc.interconnect.csr import AutoCSR, CSRStatus, CSRStorage
from litex.soc.interconnect.csr_eventmanager import EventManager, EventSourceProcess
from litex.soc.integration.soc import SoCRegion
from litex.soc.integration.soc_core import SoCCore

class TutorialGPIOIn(Module, AutoCSR):
    """Small explicit-name equivalent of LiteX GPIOIn, for robust name extraction."""
    def __init__(self, pads):
        self._input = CSRStatus(len(pads), name="input")
        self.specials += MultiReg(pads, self._input.status)


class TutorialGPIOOut(Module, AutoCSR):
    """Small explicit-name equivalent of LiteX GPIOOut."""
    def __init__(self, pads):
        self.output = CSRStorage(len(pads), reset=0, name="output")
        self.comb += pads.eq(self.output.storage)


class TutorialTimer(Module, AutoCSR):
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


class SPIDevice(Module):
    """Mode-0, MSB-first 8-bit command followed by 8-bit reply."""
    def __init__(self, clk, cs_n, mosi, miso, *, command_byte, reply_byte):
        old_clk = Signal()
        old_cs = Signal(reset=1)
        bits = Signal(5)
        command = Signal(8)
        reply = Signal(8, reset=reply_byte)
        self.comb += If(~cs_n & (bits >= 8) & (command == command_byte),
            miso.eq(reply[7])).Else(miso.eq(1))
        self.sync += [old_clk.eq(clk), old_cs.eq(cs_n),
            If(cs_n,
                If(~old_cs,
                    If(bits == 16, Display("SPI_FRAME command=0x%02x bits=%d", command, bits)),
                ),
                bits.eq(0), command.eq(0), reply.eq(reply_byte),
            ).Else(
                If(clk & ~old_clk,
                    bits.eq(bits + 1),
                    If(bits < 8, command.eq((command << 1) | mosi)),
                ),
                If(~clk & old_clk & (bits > 8), reply.eq(Cat(0, reply[:7]))),
            ),
        ]


class TutorialSPI(Module, AutoCSR):
    def __init__(self, cfg):
        # bit 0=CLK, bit 1=MOSI, bit 2=CS_N; reset leaves slave unselected.
        self.out = CSRStorage(3, reset=4, name="out")
        self.input = CSRStatus(1, name="input")
        clk, mosi, cs_n, miso = Signal(), Signal(), Signal(), Signal()
        self.comb += [clk.eq(self.out.storage[0]), mosi.eq(self.out.storage[1]),
                      cs_n.eq(self.out.storage[2]), self.input.status.eq(miso)]
        self.submodules.device = SPIDevice(clk, cs_n, mosi, miso, command_byte=cfg.spi_command, reply_byte=cfg.spi_reply)


class TutorialI2C(Module, AutoCSR):
    def __init__(self, platform, cfg):
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
            p_ADDRESS=cfg.i2c_address, i_clk=ClockSignal(), i_rst=ResetSignal(), i_scl=scl, i_sda=sda,
            o_release_sda=device_release)


class CompletionSlave(Module):
    """Simulation endpoint with delayed responses and configuration readback."""
    def __init__(self, cfg, fault, runtime):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        active = Signal()
        remaining = Signal(8)
        self.stage = Signal(4)
        operation = Signal(2)
        request = bus.cyc & bus.stb
        self.waiting = Signal()
        self.comb += [
            bus.ack.eq(request & active & (remaining == 0)), bus.err.eq(0),
            bus.dat_r.eq(Mux(bus.adr == cfg.completion_base // 4, cfg.tag,
                            Mux(bus.adr == cfg.completion_base // 4 + 1, fault,
                            Mux(bus.adr == cfg.completion_base // 4 + 4, runtime[0],
                            Mux(bus.adr == cfg.completion_base // 4 + 5, runtime[1],
                            Mux(bus.adr == cfg.completion_base // 4 + 6, runtime[2], 0)))))),
            self.waiting.eq(request & active & (remaining != 0)),
        ]
        self.sync += If(~request,
            active.eq(0),
        ).Elif(~active,
            active.eq(1), remaining.eq(runtime[3]),
            Display("BUS_WAIT adr=0x%08x we=%d clocks=%d", bus.adr, bus.we, runtime[3]),
        ).Elif(remaining != 0,
            remaining.eq(remaining - 1),
        ).Else(
            active.eq(0),
            If(bus.we,
                If(bus.adr == cfg.completion_base // 4,
                    self.stage.eq(bus.dat_w), Display("SELFTEST_STAGE id=%0d", bus.dat_w)),
                If(bus.adr == cfg.completion_base // 4 + 2,
                    Display("TIMER_ISR count=%0d op=%0d stage=%0d", bus.dat_w, operation, self.stage)),
                If(bus.adr == cfg.completion_base // 4 + 3,
                    Display("IRQ_DIAG pending=%0d", bus.dat_w)),
                If(bus.adr == cfg.completion_base // 4 + 8,
                    operation.eq(bus.dat_w[:2]),
                    Display("STRESS_OP encoded=0x%08x", bus.dat_w)),
                If(bus.adr == (cfg.completion_base + cfg.completion_size - 4) // 4,
                    If(bus.dat_w == 0x5a,
                        Display("SOC_COMPLETE data=0x%08x", bus.dat_w),
                    ).Else(Display("SOC_FAIL data=0x%08x", bus.dat_w)),
                    Finish(),
                ),
            ),
        )


class TutorialSoC(SoCCore):
    # These are selected allocations, not protocol-mandated addresses/IRQ slots.
    csr_map = {"gpio_in": 0, "gpio_out": 1, "uart": 2, "timer0": 3,
               "spi": 4, "i2c": 5, "identifier_mem": 6}
    interrupt_map = {"timer0": 0, "uart": 1}

    def __init__(self, platform, *, cfg, rom_words):
        super().__init__(platform,
            clk_freq=cfg.sys_clk_hz, cpu_type="vexriscv", cpu_variant="standard",
            cpu_reset_address=0, integrated_rom_size=cfg.rom_size,
            integrated_rom_init=rom_words, integrated_sram_size=cfg.sram_size,
            integrated_main_ram_size=cfg.main_ram_size, with_uart=False,
            with_timer=False, with_ctrl=False,
            ident="SoC Integration Tutorial Chapter 13")
        # trace=True only compiles tracing; the runtime also needs this signal high.
        self.comb += platform.trace.eq(1)
        for name in ("sram", "main_ram"):
            base, size = cfg.regions[name]
            memory_bus = getattr(self, name).bus
            self.sync += If(memory_bus.cyc & memory_bus.stb & memory_bus.ack &
                ((memory_bus.adr == base // 4) | (memory_bus.adr == (base + size - 4) // 4)),
                Display(f"MEMORY_BOUNDARY name={name} word=0x%08x we=%0d sel=%x",
                        memory_bus.adr, memory_bus.we, memory_bus.sel))
        fault = Signal(32)
        self.test_reset = Signal()
        runtime = [Signal(32) for _ in range(4)]
        self.add_module("completion", CompletionSlave(cfg, fault, runtime))
        self.bus.add_slave(name="completion", slave=self.completion.bus,
            region=SoCRegion(origin=cfg.completion_base, size=cfg.completion_size,
                             mode="rw", cached=False))
        platform.add_source(str(Path(__file__).with_name("bus_monitor.v")))
        for monitored, memory in ((self.completion.bus, 0), (self.sram.bus, 1)):
            self.specials += Instance("bus_monitor", p_MEMORY=memory,
                i_clk=ClockSignal(), i_rst=ResetSignal(), i_cyc=monitored.cyc,
                i_stb=monitored.stb, i_ack=monitored.ack, i_err=monitored.err,
                i_we=monitored.we, i_adr=monitored.adr, i_dat_w=monitored.dat_w,
                i_dat_r=monitored.dat_r, i_sel=monitored.sel, i_stage=self.completion.stage)
        gpio_input = Signal(cfg.gpio_width)
        gpio_output = Signal(cfg.gpio_width)
        self.comb += gpio_input.eq(0x55555555 & ((1 << cfg.gpio_width) - 1))
        self.add_module("gpio_in", TutorialGPIOIn(gpio_input))
        self.add_module("gpio_out", TutorialGPIOOut(gpio_output))
        old_gpio = Signal(cfg.gpio_width)
        self.sync += [old_gpio.eq(gpio_output),
            If(gpio_output != old_gpio, Display("GPIO_OUTPUT value=0x%x", gpio_output))]
        pads = Record([("tx", 1), ("rx", 1)])
        self.add_uart(name="uart", uart_name="serial", uart_pads=pads,
            baudrate=cfg.baud, fifo_depth=cfg.uart_fifo_depth, rx_fifo_rx_we=True)
        self.add_module("serial_loopback", SerialLoopback(pads, decode_cycles=cfg.bit_cycles))
        self.add_module("timer0", TutorialTimer())
        self.irq.add("timer0", use_loc_if_exists=True)
        self.add_module("spi", TutorialSPI(cfg))
        self.add_module("i2c", TutorialI2C(platform, cfg))
        old_irq = Signal()
        timer_irq = self.cpu.interrupt[self.interrupt_map["timer0"]]
        self.sync += [old_irq.eq(timer_irq),
            If(timer_irq & ~old_irq, Display("IRQ_LINE_ASSERT source=timer0")),
            If(~timer_irq & old_irq, Display("IRQ_LINE_CLEAR source=timer0"))]
        platform.add_source(str(Path(__file__).with_name("sim_control.v")))
        self.specials += Instance("sim_control",
            p_MAX_CYCLES=cfg.max_cycles, p_BIT_CYCLES=cfg.bit_cycles,
            p_RESPONSE_WAIT=cfg.response_wait, p_STRESS_BYTES=cfg.stress_bytes,
            p_TIMER_PERIOD=cfg.timer_period,
            i_clk=ClockSignal(), i_sys_rst=ResetSignal(), i_tx=pads.tx,
            i_bus_wait=self.completion.waiting, i_irq=timer_irq, i_stage=self.completion.stage,
            o_workload_seed=runtime[0], o_stress_count=runtime[1],
            o_timer_cycles=runtime[2], o_bus_delay=runtime[3],
            o_test_reset=self.test_reset, o_fault=fault)
