# 10 — Timer Events and CPU Interrupts

This chapter separates three steps that are easy to conflate: the timer reaches zero, LiteX raises an IRQ input, and the CPU accepts a machine external interrupt. The firmware tests polling, one-shot delivery, periodic delivery, and reset during the timer flow.

```text
ProjectTimer reaches zero
  → EventManager sets pending while event is enabled
  → LiteX IRQ handler drives timer0 onto VexRiscv externalInterruptArray[0]
  → firmware sets VexRiscv's source mask CSR `0xbc0` bit 0
  → mie.MEIE and mstatus.MIE allow the CPU to trap
  → mtvec enters trap_entry → isr clears timer pending → mret resumes firmware
```

There is no PLIC in this SoC. LiteX's IRQ handler connects the source directly to the VexRiscv interrupt vector. The interrupt source number is a LiteX allocation shown in the generated map; this configuration gives `timer0` input 0.

## What the SoC configures

`SoCCore` provides a 4 KiB ROM, 4 KiB integrated SRAM, and 16 KiB `main_ram`. The stack and C data live in `main_ram`. The built-in `with_timer` is disabled because this chapter creates `ProjectTimer` with explicit CSR names. `add_module()` includes it in the design; `self.irq.add("timer0")` connects its EventManager IRQ to the CPU vector.

The test's `load=600`, one-shot `load=300`, and periodic `reload=1200` are simulation parameters chosen to make transitions visible. They are not fixed Timer values. The same is true of test loop bounds and expected ISR counts.

## Why doesn't the ISR claim a PLIC source?

A PLIC has claim/complete registers and arbitrates interrupt sources in systems that include one. This LiteX VexRiscv design has no PLIC. The CPU sees the LiteX IRQ line as a machine external interrupt. In this VexRiscv RTL, CSR `0xbc0` is an additional per-source mask: bit 0 must be set for `externalInterruptArray[0]` to contribute to `mip.MEIP`. Firmware then enables `mie.MEIE` (bit 11) and global `mstatus.MIE`. All three masks must allow delivery. The ISR clears the timer's own `ev_pending` bit before `mret`. If it leaves that source pending, the IRQ stays high and the CPU can trap again immediately.

The CPU records the interrupted PC in `mepc` and updates machine trap state. `trap_entry` saves the general registers that its C handler can modify to the RAM stack, calls `isr`, restores them, then executes `mret`. This is why the startup code must set `sp` to valid RAM before enabling interrupts.

## What the tests observe

The polling phase leaves interrupts disabled and samples the decreasing counter. The one-shot phase expects one ISR. The periodic phase expects three more; the ISR clears each event so the timer can assert a new edge. Simulation logs record IRQ rise/fall, ISR counts, and a final completion write. Reset cases pulse reset while the timer is counting or while an ISR starts, then require the firmware checks to complete again.

`run.py` checks the generated memory and CSR maps before compiling firmware. The first attempt exposed a useful failure: the IRQ line rose, but the CPU did not enter the ISR until firmware set the VexRiscv-specific `0xbc0` source mask as well as the standard RISC-V interrupt bits. It also checks the generated `timer0_interrupt` assignment and saves it in `results/10/irq_map.csv`. The CPU input in this build is index 0; this is a build result, not a universal LiteX interrupt number.

```sh
PYTHONHASHSEED=0 python3 chapters/10-timer-irq/run.py
```

A PASS proves the modeled timer event reached the CPU, the handler cleared it, and firmware returned from the trap. It does not prove board-level interrupt wiring or physical timer accuracy.
