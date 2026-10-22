"""Local GPIO logic, first introduced in chapter 14."""
from migen import Module,Signal,If
from migen.genlib.cdc import MultiReg
from litex.soc.interconnect.csr import AutoCSR,CSRStatus,CSRStorage

class Heartbeat(Module):
    def __init__(self, pin, half_period):
        if half_period < 2: raise ValueError('heartbeat half-period must be >= 2 clocks')
        counter=Signal(max=half_period)
        self.sync += If(counter==half_period-1, counter.eq(0),pin.eq(~pin)).Else(counter.eq(counter+1))

class ButtonInput(Module, AutoCSR):
    def __init__(self, pins):
        synced=Signal(len(pins))
        self.input=CSRStatus(len(pins),name='input')
        self.specials += MultiReg(pins,synced,n=2)
        self.comb += self.input.status.eq(synced)

class LEDOutput(Module, AutoCSR):
    def __init__(self, pins):
        self.output=CSRStorage(len(pins),name='output')
        self.comb += pins.eq(self.output.storage)
