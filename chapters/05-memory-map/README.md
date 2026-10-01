# 05 — Explicit Memory Map and Decode

## Integration change

Connect ROM, SRAM and a register endpoint to one Wishbone main bus with an explicit byte-address map. The map checker validates alignment, range overlap and holes before the CPU simulation starts.

| Region | Byte address | Size | Access |
| --- | ---: | ---: | --- |
| ROM | `0x00000000–0x00000fff` | 4 KiB | Fetch and read |
| SRAM | `0x00010000–0x00010fff` | 4 KiB | Read/write and stack |
| Registers | `0x20000000–0x20000fff` | 4 KiB | Probe and completion |

The CPU issues byte addresses through AXI-Lite. The LiteX bridge presents word addresses to this 32-bit Wishbone bus; for example, `0x00010ffc / 4 = 0x000043ff`.

## Run and acceptance

```sh
PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py
```

The nominal firmware checks the ROM boundary word, SRAM first/last words, and register readback before writing the completion code. The negative firmware loads from `0x30000000`; the CPU trap handler must report `mcause=5` (load access fault) and the fault marker. It must not report normal completion. The map unit check must reject a deliberately overlapping region.

Evidence is written under `results/05/` and `results/05-unmapped/`; this includes the declared map, LiteX-generated map, firmware images, logs and waveforms.

## Decode constraints

- A request must select exactly one address region. Overlap is a build-time error.
- A hole has no target; it must not alias a neighboring device or return stale data.
- Decode selects the responder. It does not arbitrate multiple masters or define access permissions.
- Registered endpoint ACKs ensure that a response belongs to the currently selected transaction.
