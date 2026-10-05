# 08 — Reading and Driving GPIO through LiteX CSR

This stage connects four GPIO outputs and four GPIO inputs to the SoC. Bare-metal C writes `0x0`, then `0xa` to the output CSR. The simulation changes the external input pins from `0x0` to `0x5` after 1000 system-clock cycles. The CPU must observe both values by reading the input CSR.

```text
C gpio_out_output_write(0xa)
      │ CPU store → AXI-Lite → LiteX AXILite2Wishbone → Wishbone decode
      ▼
CSR bridge → CSRStorage → gpio_out[3:0] = 1010

gpio_in pins = 0101 → two-stage MultiReg synchronizer → CSRStatus
                                                         │ CPU load
                                                         └──> C reads 0x5
```

## Questions and answers

### What SoC settings does this GPIO experiment rely on?

The `SoCCore` configuration keeps a 4 KiB ROM, 4 KiB integrated SRAM, and 16 KiB main RAM for the bare-metal C image, while disabling the default UART, Timer, and control block. The GPIO banks are project modules with their own CSRs; they are not LiteX's `GPIOIn`/`GPIOOut` instances. `GPIOInput` combines `CSRStatus(4)` with a two-stage `MultiReg`, while `GPIOOutput` combines `CSRStorage(4, reset=0)` with a direct pin assignment. The width and reset value describe the pin bank, not a memory region.

Adding these CSR banks changes CSR allocation: bank names and register names become part of the generated software interface. Keep the module names, explicit CSR names, generated `csr.h`, and firmware build from the same SoC configuration. Changing `csr_paging` or adding another CSR bank can move later bank addresses; code should consume the newly generated header rather than preserve numeric addresses by hand.

### What is a CSR, and how does C access it?

A CSR is a small control/status register exposed to software at an address. LiteX Builder assigns the CSR bank and register addresses and generates `generated/csr.h`, which provides C accessors such as `gpio_out_output_write()` and `gpio_in_input_read()`. These accessors ultimately cause ordinary CPU load/store transactions through the CSR bridge. The GPIO is not directly connected to a C variable.

### Why is the input CSR read-only?

Input state comes from the pins. Software can sample it, but writing a CSR must not change an external input. The program deliberately attempts a raw write to the generated input address, reads again, and requires the value to remain `0x5`. This rejects a fake model where software can write the value it later claims to have observed.

### What does `MultiReg` do?

The simulated input pins are external to the local clocked logic. `MultiReg` samples them through two local-clock stages, reducing the chance that a metastable value propagates into the rest of the design. The CPU sees the synchronized value a little later than the pin changes. This simulation demonstrates the path; it does not replace board-level CDC and electrical review.

### Why generate `csr.h` before compiling C?

Adding CSR banks can move other CSR addresses. In this stage, the generated `gpio_in_input` is at `0xf0000000` and `gpio_out_output` at `0xf0000800`; the identifier CSR shifts after the new banks are added. The runner first elaborates this exact SoC, generates and checks `csr.csv` and `csr.h`, then compiles C against that header. It builds the same SoC again with the compiled ROM and verifies the map again. That keeps the software names and hardware addresses aligned.

### How do the logs show that the CPU saw the input change?

`GPIO_INPUT_DRIVE value=0x5` records the simulation changing the pads. `SOC_PROBE data=0x00000000` and later `SOC_PROBE data=0x00000005` are writes made by the CPU after its reads. The runner checks their order, in addition to `GPIO_OUTPUT value=0xa`. A final value alone would not prove that the CPU first observed zero and then observed the change.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/08-gpio/run.py
```

The run should show the output transition, the CPU's initial input observation, the driven input transition, the CPU's new observation, then `SOC_COMPLETE`. Inspect `results/08/builder/csr.csv`, `csr-header.txt`, `memory_map.csv`, `firmware/program.map`, `run.log`, and `builder/gateware/sim.vcd`. In the waveform, correlate `gpio_in`, `gpio_out`, CSR bus activity, and the two input synchronizer stages.

## What does a PASS prove?

The generated-map check proves the software CSR addresses match this SoC. The ordered log and readback check prove the CPU drove the output, observed the externally changed input through the synchronized path, and could not alter that input with a write. The simulation uses polling; it does not test GPIO interrupts or board pin constraints.
