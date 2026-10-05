# 11 — SPI and I²C: Who Drives Each Bit?

UART sends bytes over one timed serial line. SPI and I²C also select a device or send an address. This stage has VexiiRiscv C code bit-bang the pins through CSR reads and writes. Independent responder models decode the serial waveforms and provide the return data; the test does not manufacture a successful read by directly returning the expected C value.

```text
SPI: CPU → spi_out CSR → CLK/MOSI/CS_N → SPI device model
                                  MISO ← device model → spi_input CSR → CPU

I²C: CPU → i2c_out CSR → SCL/SDA open-drain line → 0x42 device model
                             SDA ACK/data ← model → i2c_input CSR → CPU
```

## Which LiteX settings form this bit-bang SoC?

`SoCCore` provides the CPU, reset-at-zero ROM, 4 KiB on-chip SRAM, and 16 KiB main RAM for the freestanding C program. The default UART, Timer, and control block are disabled. SPI and I²C here are small `AutoCSR` modules, not hardware controllers: `CSRStorage` drives output pins, `CSRStatus` samples input pins, and C toggles those values to create each protocol edge. The completion register is a separate uncached Wishbone region at `0x80000000`.

The widths and reset values are protocol state: SPI's 3-bit output resets to `4`, leaving active-low `CS_N` high; I²C's 2-bit output resets to `3`, releasing SCL and SDA. Changing either reset value can select the SPI device at boot or hold an I²C line low before START. Adding or renaming CSR banks changes generated CSR addresses, so the runner regenerates the header and compiles the C firmware against it. This pin-level approach is intentionally slow; replacing it with LiteX controllers changes the CSR interface and moves timing generation from software into hardware.

The SPI mode 0, `0x9f` command, `0xa5` model response, and I²C 7-bit address `0x42` are the choices for these device models and firmware. They are not requirements for every SPI or I²C device. To change the I²C address, update both the C transaction and `i2c_device.v`; `0x84` and `0x85` are derived wire bytes `(0x42 << 1) | R/W`. To change the SPI command or reply, update the CPU check and model together. The `0x86` address is deliberately wrong to exercise NACK.

## Questions and answers

### How does the SPI transaction work?

The CPU lowers active-low `CS_N`, sends command `0x9f` MSB first, then supplies eight more clocks while the model returns `0xa5` on MISO. This is mode 0: clock idles low and both ends sample on rising edges. The model records one `SPI_FRAME command=0x9f bits=16`, and the CPU records the returned byte in `PROTOCOL_PROBE`.

The negative case leaves `CS_N` high. The CPU still toggles the clock, but the model must ignore the frame; MISO reads the idle high value `0xff`, and no valid `SPI_FRAME` is logged. That separates “clock changed” from “the intended device was selected.”

### Why is I²C SDA released instead of driven high?

I²C uses an open-drain line. A device can pull SDA low or release it; the pull-up makes a released line read high. If both master and slave drive high actively, they are not modeling the wired-AND behavior correctly. In the model, SDA is high only when both sides release it.

### What are the I²C address bytes?

The device's 7-bit address is `0x42`. The wire byte combines it with the read/write bit: `0x84` for write and `0x85` for read. The CPU first sends wrong address `0x86` and must receive NACK. A valid write sends START, address `0x84`, register index, data, and STOP. For a read, the CPU selects the register with a write-address phase, issues a repeated START, sends `0x85`, receives one byte, then releases SDA for NACK on the ninth clock before STOP.

### What does the device model prove?

`i2c_device.v` independently samples line transitions, checks the address and ACK bit, records register writes, and drives read data. The CPU reads back `0x5a` and `0xc3`; the model also logs those bytes. The runner requires both protocol logs and CPU probe values, plus two master NACKs after the one-byte reads. During development, reversing the model's release/data bit returned `0xa5` instead of `0x5a`; the CPU comparison exposed it.

### Why are these devices CSR pins instead of full LiteX controllers?

The goal here is to make every edge and bit ownership visible. `spi_out` and `i2c_out` are CSRStorage values that drive pins; `spi_input` and `i2c_input` expose pin state through CSRStatus. They are not full SPI/I²C controller IP. This deliberately small design lets us inspect protocol timing before adding controller FIFOs or DMA.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/11-spi-i2c/run.py
```

The runner checks the generated CSR addresses before and after the firmware build. Expected evidence includes the 16-bit SPI frame, NACK for `0x86`, ACKs for `0x84`/`0x85`, both register readbacks, master NACKs, and `SOC_COMPLETE`. Inspect `results/11/run.log`, `builder/csr.csv`, the CSR header, firmware map, and `builder/gateware/sim.vcd`. In the waveform, verify MOSI is stable around SPI rising edges and check I²C SDA START/STOP transitions and ninth-bit ACK/NACK.

## What does a PASS prove?

The pass proves the CPU-generated pin sequence was recognized by the independent models, valid SPI/I²C responses returned through CSR pin reads, bad chip select and address were rejected, and firmware compared the returned bytes successfully. It does not claim that a LiteX hardware SPI or I²C controller has been integrated; that remains a separate implementation step.
