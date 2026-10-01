# 04 — Writable SRAM and Stack Region

## Integration change

Add a 4 KiB Wishbone SRAM at byte address `0x00010000`. The CPU boots from ROM, exercises the first and last SRAM words, applies byte and halfword stores, and uses the SRAM region for a function call stack.

The firmware expects the first word to read back as `0xbbcc33aa` after full-word and partial-lane updates. It also writes and reads the final word at `0x00010ffc`, then reports completion through the register endpoint.

## Run and acceptance

```sh
PYTHONHASHSEED=0 python3 chapters/04-sram/run.py
```

The runner executes a nominal 4 KiB configuration and a 256-byte negative configuration. The nominal run must complete with the expected readback value. The undersized run must report `mcause=7` (store access fault) and the expected fault marker without a normal completion marker.

Outputs are stored in `results/04/` and `results/04-small-ram/`, including ROM/RAM images, maps, run logs and VCD traces.

## Memory and ABI constraints

- The SRAM model is a LiteX Wishbone behavioral memory. Replacing it with an FPGA block RAM or ASIC SRAM macro requires matching port width, read latency, write-mask behavior and initialization.
- Wishbone `adr` is word-addressed in this integration. Byte address `0x00010000` corresponds to word address `0x4000`.
- The stack grows down from the configured top. Firmware explicitly adjusts `sp`, saves `ra` in SRAM before nested calls, restores it before returning, and keeps stack alignment.
- The stack reservation and last-word boundary test occupy distinct SRAM locations.
