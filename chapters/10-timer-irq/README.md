# 10 — From Timer Polling to a CPU Interrupt

Stage 09 polled the UART status register: the CPU repeatedly asked whether a byte had arrived. This stage first polls a timer value, then lets the timer raise an interrupt. Firmware checks one one-shot interrupt and three periodic interrupts, clears each request, stops the timer, and verifies that no extra ISR runs.

```text
timer counts to zero
  → event pending is set
  → event enable raises timer0 IRQ
  → PLIC source 1 is enabled and CPU interrupt masks allow delivery
  → VexiiRiscv jumps to mtvec / trap_entry
  → save registers → claim PLIC source → clear timer pending
  → complete PLIC claim → restore registers → mret
  → resume interrupted main code
```

## What LiteX configuration connects the timer to the CPU?

The SoC uses a 1 MHz clock, reset-at-zero CPU, 4 KiB ROM, 4 KiB on-chip SRAM, and 16 KiB main RAM. Main RAM holds C data, the stack, and the trap handler's saved registers. The built-in `with_timer` option is disabled because this chapter instantiates its explicitly named `ProjectTimer` instead. `add_module("timer0", ...)` adds the CSR/event logic, and `self.irq.add("timer0", use_loc_if_exists=True)` routes its event through LiteX's IRQ infrastructure; the generated map places it at PLIC source 1 in this build.

`load` and `reload` are counts of `sys` clock cycles, not microseconds: with a 1 MHz clock, 1200 counts are about 1.2 ms. Changing `clk_freq` changes elapsed time but not the count values; changing `reload` from zero to a positive value changes a one-shot into a periodic event. The test and firmware must agree on both settings.

## Questions and answers

### What must be enabled before the CPU enters the ISR?

The timer event must be enabled, PLIC source 1 must have nonzero priority and be enabled, the CPU machine-external interrupt mask (`mie.MEIE`) must be set, the global machine interrupt enable (`mstatus.MIE`) must be set, and `mtvec` must point to the trap entry. A pending bit records that an event happened; by itself it does not guarantee delivery.

### Why is the timer implemented in this chapter instead of using `Timer()` directly?

With this pinned Python/Migen combination, LiteX's `Timer()` cannot infer stable CSR names and fails during construction. `ProjectTimer` spells out its named CSRs, down-counter, and `EventManager` connection while using LiteX `CSRStorage`, `CSRStatus`, and `EventSourceProcess`. This is actual hardware logic: count reaching zero sets pending and the event path drives the IRQ. It is not Python code pretending to call an ISR.

### What is the difference between `pending` and `enable`?

`pending` records an event that occurred. `enable` controls whether that event is allowed to raise the IRQ line. The polling phase reads a decreasing count with the interrupt disabled. The one-shot phase uses `reload=0`, so it should interrupt once. The periodic phase reloads 1200 and should interrupt three more times.

### Why must the ISR claim and complete the PLIC request?

The ISR reads the PLIC claim register to identify source 1, clears the timer pending bit, then writes the claim ID back to complete the PLIC transaction. If it returns without clearing the source, the IRQ line remains asserted and the CPU can re-enter immediately, producing an interrupt storm. The test checks for ISR re-entry and puts finite bounds on all waits.

### What do the reset cases verify?

One run resets the SoC while the timer is counting; another resets when the first ISR probe is written. After release, the CPU must restart from ROM and complete polling, all four expected ISR observations, and the final marker again. The reset-injection counter lives in a `por` domain that the system reset does not clear, so the reset pulse occurs once.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py
```

The normal log contains `TIMER_POLL`, four `IRQ_LINE_ASSERT/CLEAR` pairs, `TIMER_ISR` values `(phase,count) = (1,1), (2,2), (2,3), (2,4)`, and `SOC_COMPLETE`. The two reset runs are under `results/10-reset-count/` and `results/10-reset-isr/`. Inspect `builder/csr.csv`, `irq_map.csv`, `firmware/program.map`, `run.log`, and the VCD. Follow timer count, pending, IRQ, the CPU external-interrupt input, ISR probes, then `mret`/return to main.

## What does a PASS prove?

The CSR map proves the timer registers and IRQ source were constructed. The IRQ-line transitions prove hardware requested service. ISR counters and the final completion prove the CPU received, acknowledged, and returned from each interrupt. The reset cases prove the software path can restart cleanly. These checks cover the simulated VexiiRiscv PLIC path, not board-level interrupt wiring.
