# 05 — Who Answers an Address?

This stage connects ROM, SRAM, and a register endpoint to one Wishbone main bus. It declares a byte-address map, checks for alignment and overlap, then runs firmware that touches the first and last words of each region.

| Region | Byte-address range | Size | Purpose |
| --- | --- | ---: | --- |
| ROM | `0x00000000–0x00000fff` | 4 KiB | Firmware and reset code |
| SRAM | `0x00010000–0x00010fff` | 4 KiB | Writable data and stack |
| Registers | `0x20000000–0x20000fff` | 4 KiB | Probe/readback and completion |

## What does address decoding do?

The decoder uses an address to select which target may answer a request. For example, an access at `0x00010000` should reach SRAM, while an access at `0x20000000` should reach the register endpoint. A well-formed map assigns a given address to at most one target. A hole has no target and should not accidentally alias a nearby memory.

The map checker in `memory_map.py` is a software-side consistency check. LiteX's bus regions provide the actual integration in this stage. The CSV records both byte and word addresses so that the address-unit conversion can be inspected.

## Questions and answers

### Why does Wishbone show a different address from firmware?

Firmware and the map use byte addresses. This chapter's 32-bit Wishbone interface uses word addresses, where each step represents four bytes. For example, SRAM's final word is at byte address `0x00010ffc`; the bus sees `0x00010ffc / 4 = 0x000043ff`. The data and byte select still determine which bytes within that word are used.

### Is address decode the same as arbitration?

No. Decode chooses a responder based on the address. Arbitration decides which master may use a shared bus when several masters request it. This stage has one CPU master, so it tests decode and response behavior without adding multi-master arbitration.

### What happens for overlapping or unmapped addresses?

An overlap is rejected before CPU simulation because two regions would claim the same address. The unit test deliberately adds an overlapping region and expects `validate()` to raise an error. For an unmapped read at `0x30000000`, no target responds. The CPU trap handler records `mcause=5` (load access fault) at the test endpoint, and the runner requires the fault marker with no normal completion.

### How do we know which part failed?

There are separate observations for each boundary: the map checker identifies overlap before building; the bus address and selected region show where a valid request should go; and the CPU trap handler records the architectural load fault if no region responds. The trace and run log let us distinguish a bad map from an ordinary firmware value mismatch.

### Does a declared map create the decoder?

No. A table or CSV alone is only a contract. In this chapter, the LiteX SoC regions attach the ROM, `wishbone.SRAM`, and register slave to the main bus. The map checker verifies the intended byte ranges and catches errors early. Later, Stage 06 compares that hand-written contract with LiteX Builder's generated map.

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py
```

The normal firmware checks the first and final ROM words, first and final SRAM words, and register readback before writing completion. The negative firmware loads from unmapped address `0x30000000`. Inspect `results/05/memory_map.csv`, `results/05/run.log`, and the corresponding output under `results/05-unmapped/`.

An endpoint ACK is registered so its response is aligned with the selected transaction. ACK means the request has completed; data that happens to be visible on a bus without an ACK is not a completed read.

## What does a PASS prove?

The map unit test proves that the declared regions are aligned, non-overlapping, and selected at their boundaries. The normal CPU run proves accesses reached the intended targets. The unmapped test proves a hole becomes a load access fault instead of stale data or a false completion. Stage 06 then asks LiteX to generate the SoC map and checks the firmware contract against it.
