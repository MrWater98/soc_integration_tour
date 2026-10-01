# 03 — Firmware ROM Boot

## Integration change

Replace the inline instruction list with this stage's assembled RV32 firmware. The build produces ELF, flat binary, word-oriented hex, a fixed-depth ROM initialization image, and SHA-256 files. LiteX's CPU reset address and integrated ROM both start at byte address `0x00000000`.

| Region | Byte address | Size | Use |
| --- | ---: | ---: | --- |
| ROM | `0x00000000–0x000003ff` | 1 KiB | Reset and firmware |
| Completion endpoint | `0x20000000–0x20000fff` | 4 KiB | Firmware pass marker |
| CSR | `0xf0000000–0xf000ffff` | 64 KiB | LiteX control/status space |

The endpoint ACK is registered. This keeps the bridge response aligned with the target transaction and avoids sampling a stale read value.

## Run and acceptance

```sh
PYTHONHASHSEED=0 python3 chapters/03-rom/run.py
```

The run rejects empty/oversized ROM images and misaligned/out-of-range reset addresses before simulation. The CPU simulation must log a fetch at address zero and the firmware completion value `0x35`. Generated artifacts are under `results/03/`.

## Image and address contract

- RISC-V firmware is little-endian. `program.bin` is byte-oriented; `program.hex` contains one 32-bit word per line; `rom_init.hex` fills all 256 ROM words.
- Memory maps use byte addresses. A Wishbone word address is the aligned byte address divided by four; completion byte address `0x20000000` maps to Wishbone address `0x08000000`.
- The generated `memory_map.csv` is compared with the firmware address contract before RTL simulation.

The ROM stage is accepted only when both the image checks and the CPU completion marker pass.
