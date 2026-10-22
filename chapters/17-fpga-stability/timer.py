"""Explicit-name Timer logic, first exercised in chapter 10."""
from migen import Module,Signal,If
from litex.soc.interconnect.csr import AutoCSR,CSRStatus,CSRStorage
from litex.soc.interconnect.csr_eventmanager import EventManager,EventSourceProcess
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
