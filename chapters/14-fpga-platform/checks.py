"""Portable heartbeat and input-synchronizer checks for this chapter."""

def check_logic(result):
    """Small portable simulations for counter and two-stage button synchronization."""
    from migen import Signal
    from migen.sim import run_simulation
    from io_cores import Heartbeat,ButtonInput
    samples=[];pin=Signal();heartbeat=Heartbeat(pin,4)
    def stimulus():
        for _ in range(17):
            samples.append((yield pin));yield
    run_simulation(heartbeat,stimulus(),vcd_name=str(result/'heartbeat.vcd'))
    changes=[i for i in range(1,len(samples)) if samples[i]!=samples[i-1]]
    if len(changes)<3 or any(b-a!=4 for a,b in zip(changes,changes[1:])):raise AssertionError(f'wrong heartbeat spacing {changes}')
    pins=Signal(2);buttons=ButtonInput(pins)
    captured=[]
    def button_stimulus():
        yield pins.eq(3)
        for _ in range(5):captured.append((yield buttons.input.status));yield
        if (yield buttons.input.status)!=3:raise AssertionError('button synchronizer did not propagate input')
    run_simulation(buttons,button_stimulus(),vcd_name=str(result/'button-sync.vcd'))
    if captured[0]!=0:raise AssertionError('async button bypassed synchronizer')
    return dict(heartbeat_transition_samples=changes,half_period=4,button_samples=captured)
