"""One 32-bit Wishbone Classic register, with optional faults for the lesson."""

from pathlib import Path
import subprocess
import sys


CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path

add_litex_to_path(ROOT)

# This file is both the reusable implementation and a convenient chapter entry point.
if __name__ == "__main__":
    verify = Path(__file__).with_name("verify.py")
    raise SystemExit(subprocess.call([sys.executable, str(verify), *sys.argv[1:]]))

from migen import Cat, If, Module, Replicate, Signal
from litex.soc.interconnect import wishbone


BYTE_ADDRESS = 0x1000
WORD_ADDRESS = BYTE_ADDRESS // 4


class RegisterSlave(Module):
    def __init__(self, wait_cycles=0, fault=None):
        if wait_cycles < 0 or wait_cycles > 15:
            raise ValueError("wait_cycles must be in the range 0..15")
        if fault not in (None, "no_ack", "early_ack", "held_ack"):
            raise ValueError(f"unknown fault mode: {fault}")
        self.bus = bus = wishbone.Interface(data_width=32, address_width=32, addressing="word")
        self.value = Signal(32, reset=0x11223344)

        IDLE, WAIT, RESP, HOLD = range(4)
        state = Signal(2, reset=IDLE)
        remaining = Signal(4)
        write = Signal()
        data = Signal(32)
        sel = Signal(4)
        mask = Cat(*(Replicate(sel[i], 8) for i in range(4)))
        request = bus.cyc & bus.stb

        if fault == "early_ack":
            self.comb += bus.ack.eq(1)
        elif fault == "held_ack":
            self.comb += bus.ack.eq((state == RESP) | (state == HOLD))
        else:
            self.comb += bus.ack.eq((state == RESP) & request)
        self.comb += [bus.dat_r.eq(self.value), bus.err.eq(0)]

        self.sync += [
            If(state == IDLE,
                If(request & (bus.adr == WORD_ADDRESS),
                    write.eq(bus.we),
                    data.eq(bus.dat_w),
                    sel.eq(bus.sel),
                    remaining.eq(wait_cycles),
                    state.eq(WAIT),
                ),
            ).Elif(state == WAIT,
                If(~request,
                    state.eq(IDLE),
                ).Elif(remaining != 0,
                    remaining.eq(remaining - 1),
                ).Elif(fault != "no_ack",
                    state.eq(RESP),
                ),
            ).Elif(state == RESP,
                If(request & write, self.value.eq((self.value & ~mask) | (data & mask))),
                state.eq(HOLD),
            ).Elif(state == HOLD,
                If(~request, state.eq(IDLE)),
            ),
        ]
