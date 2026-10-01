"""A minimal native VexiiRiscv SoC with an instruction ROM and write target."""
from migen import Display, Finish, If, Module, Signal, Cat, Constant
from litex.soc.interconnect import wishbone
from litex.soc.integration.soc import SoCRegion, SoCIORegion
from litex.soc.integration.soc_core import SoCCore


class WriteTarget(Module):
    def __init__(self, *, no_ack=False):
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        request = bus.cyc & bus.stb
        byte_address = Signal(32)
        self.comb += byte_address.eq(Cat(Constant(0, 2), bus.adr[:30]))
        self.comb += [bus.dat_r.eq(0), bus.err.eq(0)]
        if no_ack:
            self.comb += bus.ack.eq(0)
            wait_seen = Signal()
            self.sync += If(request & bus.we & ~wait_seen,
                wait_seen.eq(1),
                Display("DATA_WAIT byte_address=0x%08x value=0x%08x", byte_address, bus.dat_w))
        else:
            self.sync += [bus.ack.eq(0), If(request & ~bus.ack, bus.ack.eq(1))]
            self.sync += If(request & ~bus.ack & bus.we,
                If((bus.adr == 0x10) & (bus.dat_w == 0x40) & (bus.sel == 0xf),
                    Display("PASS 01: VexiiRiscv wrote 0x40 to byte address 0x40"),
                ).Else(Display("FAIL 01: wrong write")), Finish())


class ProjectSoC(SoCCore):
    def __init__(self, platform, *, no_ack=False):
        # addi x1,x0,64; sw x1,0(x1); jal x0,0.
        words = [0x04000093, 0x0010a023, 0x0000006f] + [0x00000013] * 13
        super().__init__(platform, clk_freq=1_000_000, cpu_type="vexiiriscv",
            cpu_variant="standard", cpu_reset_address=0,
            integrated_rom_size=0x40, integrated_rom_init=words,
            integrated_sram_size=0, integrated_main_ram_size=0,
            with_uart=False, with_timer=False, with_ctrl=False)
        self.bus.add_region("io_low", SoCIORegion(origin=0x40, size=0x40))
        self.add_module("write_target", WriteTarget(no_ack=no_ack))
        self.bus.add_slave(name="write_target", slave=self.write_target.bus,
            region=SoCRegion(origin=0x40, size=0x40, mode="rw", cached=False))
        rom_bus = self.rom.bus
        seen_first = Signal()
        rom_byte_address = Signal(32)
        self.comb += rom_byte_address.eq(Cat(Constant(0, 2), rom_bus.adr[:30]))
        self.sync += If(rom_bus.cyc & rom_bus.stb & rom_bus.ack & ~seen_first,
            seen_first.eq(1), Display("FETCH first_byte_address=0x%08x", rom_byte_address))
        if no_ack:
            cycles = Signal(12)
            self.sync += [cycles.eq(cycles + 1), If(cycles == 600,
                Display("PASS 01-NO-ACK: write request waited without ACK"), Finish())]
