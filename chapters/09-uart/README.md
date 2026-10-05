# 09 — UART from CPU Store to TX Pin and Back

A UART write is not an immediate pin change. A byte enters a transmit FIFO, then the PHY serializes it over TX one bit at a time. This stage has the CPU send `U`, `HELLO`, and `123456`, loops the TX pin back to RX, reads received bytes from the UART FIFO, and echoes the last `6`. Both the external pin monitor and the CPU must observe `UHELLO1234566`.

```text
CPU store → CSR bridge → UART TX FIFO → UART PHY → TX pin
                                                   │ 8N1 waveform
                                                   └── loopback ──> RX pin
CPU load  ← CSR bridge ← UART RX FIFO ← UART PHY ←───────────────┘
```

## Which LiteX settings control the UART behavior?

`SoCCore` is built at `SYS_CLK_HZ = 1_000_000`, then the project explicitly adds `UART` with `baudrate=100_000`, `fifo_depth=4`, and `rx_fifo_rx_we=True`. The first two timing values work together: `BIT_CYCLES = SYS_CLK_HZ // BAUD = 10`, so one UART bit lasts ten system clocks. If `clk_freq` changes, update the simulation clock and the monitor's `decode_cycles` as well; otherwise the UART and observer will disagree about bit timing. `fifo_depth=4` is why four queued bytes can fill TX FIFO; changing it changes the expected `txfull` observation. `rx_fifo_rx_we=True` makes a read of `rxtx` consume the received byte.

The default UART is disabled in `SoCCore` (`with_uart=False`) so the design has only the explicitly named `serial` instance and stable CSR names. The UART's event interrupt is present but `ev_enable` remains off: this experiment polls status. Enabling events changes the CSR/IRQ behavior and requires firmware to configure and service that interrupt.

## Questions and answers

### What does 8N1 mean?

Each frame has one low start bit, eight data bits sent least-significant bit first, no parity bit, and one high stop bit. At the configured 100000 bit/s with a 1 MHz clock, one bit lasts about ten system clocks. TX idles high. The simulation loopback only wires the pins; its monitor decodes the TX waveform instead of copying the CPU's intended byte.

### Why check both TX and RX bytes?

`UART_TX_BYTE` comes from decoding the actual TX pin waveform. `UART_RX_BYTE` is emitted after the CPU reads a byte from the RX FIFO and reports it to the test endpoint. Matching ordered streams show both the serial output and the receiver path worked. A CSR write alone proves only that software submitted a byte to the peripheral.

### What do the FIFO flags tell us?

`txfull=1` means the transmit FIFO cannot accept another byte at that moment; it does not mean the current frame has finished shifting out. `rxempty=1` means the CPU has no received byte to read. The C program uses bounded polling loops so a stuck transmitter or receiver becomes a failure instead of an infinite simulation.

### Why generate CSR addresses before compiling the firmware?

The runner first elaborates this UART-equipped SoC and checks the generated `csr.csv`. For example, `uart_rxtx` is at `0xf0000800`, `uart_txfull` at `0xf0000804`, and `uart_rxempty` at `0xf0000808`. It then compiles against the generated `csr.h`, and the final SoC build checks the same map. This prevents stale CSR constants after adding a peripheral.

### What does the wrong-baud case tell us?

The UART and CPU continue to run at the correct timing, but the external monitor is deliberately changed from ten to twelve clocks per bit. It decodes incorrect bytes, such as `0x55` being read as `0xa9`, so the test rejects the monitor result even though the CPU's internal loopback still works. This separates a peripheral failure from an observer configured with the wrong baud rate.

### Why reset in the middle of a frame?

The test asserts reset after the TX start bit but before that frame completes. It requires evidence of the incomplete frame and reset, then checks that the CPU restarts from ROM and retransmits and receives the full stream. A separate always-on simulation counter ensures the reset pulse occurs once rather than repeating after the CPU resets.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/09-uart/run.py
```

The run covers normal transmit/receive, a deliberately misconfigured monitor, and reset during TX. Evidence is in `results/09/run.log`, `wrong-baud.log`, `09-reset-tx/run.log`, `builder/csr.csv`, the generated CSR header, and the VCD. In the waveform, start at a TX falling edge, count ten system clocks per bit, and compare the decoded byte with the log.

## What does a PASS prove?

The normal PASS proves the CPU submitted bytes, LiteX UART put their 8N1 frames on TX, the looped-back receiver delivered the expected bytes, the FIFO full condition was observed, and the echoed final byte was correct. The negative PASS proves the external monitor detects its own wrong timing. The reset case proves firmware recovers from a partial transmission. It is a simulation of the UART pins, not a board electrical test.
