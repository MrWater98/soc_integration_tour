# 05 — Who Answers an Address?

This stage connects ROM, SRAM, and a register endpoint to one Wishbone main bus. It declares a byte-address map, checks for alignment and overlap, then runs firmware that touches the first and last words of each region.

| Region | Byte-address range | Size | Purpose |
| --- | --- | ---: | --- |
| ROM | `0x00000000–0x00000fff` | 4 KiB | Firmware and reset code |
| SRAM | `0x00010000–0x00010fff` | 4 KiB | Writable data and stack |
| Registers | `0x20000000–0x20000fff` | 4 KiB | Probe/readback and completion |

These bases and 4 KiB sizes are this SoC's selected map, not addresses required by Wishbone or LiteX. Moving or resizing a region means updating the `SoCRegion`, the software-side `REGIONS`/CSV contract, firmware addresses, and the generated-map check together. The aligned, non-overlapping regions are the invariant; the particular numbers are project choices.

## What does address decoding do?

The decoder uses an address to select which target may answer a request. For example, an access at `0x00010000` should reach SRAM, while an access at `0x20000000` should reach the register endpoint. A well-formed map assigns a given address to at most one target. A hole has no target and should not accidentally alias a nearby memory.

The map checker in `memory_map.py` is a software-side consistency check. LiteX's bus regions provide the actual integration in this stage. The CSV records both byte and word addresses so that the address-unit conversion can be inspected.

## How do LiteX region declarations become real connections?

This stage still uses `SoCCore` for the CPU, main bus, and ROM, but sets the integrated SRAM size to zero and explicitly creates `wishbone.SRAM(4096)`. `bus.add_slave(..., region=SoCRegion(...))` attaches the SRAM and custom register slave to the main bus; LiteX uses each region's `origin` and `size` to select a responder. The register also has a `SoCIORegion` entry and `cached=False`; SRAM is marked `cached=True`. These are region attributes, not cache hardware. This project uses VexRiscv `minimal`, which has no cache, so every access reaches the bus; the attributes document how a cache-capable variant should treat each region. `memory_map.py` is a second, software-side contract and checker; it does not replace these LiteX connections.

Keep these values aligned: the SoC declares a 4 KiB ROM, a 4 KiB SRAM at `0x10000`, and a 4 KiB register range at `0x20000000`. `REGIONS`, `memory_map.py`, firmware addresses, and the Builder output should agree. When moving or resizing one region, check for overlap, confirm firmware still accesses the intended target, and regenerate/check the CSV. `cached=False` records the device-memory policy for a cache-capable CPU. With this chapter's cache-free `minimal` core, reads and writes already reach the bus each time.

## Questions and answers

### Why does Wishbone show a different address from firmware?

Firmware and the map use byte addresses. This chapter's 32-bit Wishbone interface uses word addresses, where each step represents four bytes. For example, SRAM's final word is at byte address `0x00010ffc`; the bus sees `0x00010ffc / 4 = 0x000043ff`. The data and byte select still determine which bytes within that word are used.

### Is address decode the same as arbitration?

No. Decode chooses a responder based on the address. Arbitration decides which master may use a shared bus when several masters request it. This stage has one CPU master, so it tests decode and response behavior without adding multi-master arbitration.

### What happens for overlapping or unmapped addresses?

An overlap is rejected before CPU simulation because two regions would claim the same address. The unit test deliberately adds an overlapping region and expects `validate()` to raise an error. `0x30000000` is the chosen hole for this negative test; any address outside all configured regions should have the same unmapped behavior. The load request remains active without an ACK. The VexRiscv `minimal` RTL does not convert this Wishbone no-response case into the load-access trap this test originally assumed, so the runner checks the bus request itself rather than inventing an `mcause` result.

### How do we know which part failed?

There are separate observations for each boundary: the map checker identifies overlap before building; the bus address and selected region show where a valid request should go; and a bounded test monitor records the unanswered Wishbone request when no region responds. The minimal core does not turn this missing response into an architectural load fault. The trace and run log distinguish a bad map from a firmware value mismatch.

### Does a declared map create the decoder?

No. A table or CSV alone is only a contract. In this chapter, the LiteX SoC regions attach the ROM, `wishbone.SRAM`, and register slave to the main bus. The map checker verifies the intended byte ranges and catches errors early. Later, Stage 06 compares that hand-written contract with LiteX Builder's generated map.

## Run and inspect
The RTL snapshots for the normal and unmapped-address builds are in [`results/05/rtl`](../../results/05/rtl) and [`results/05-unmapped/rtl`](../../results/05-unmapped/rtl). Each has the generated SoC top, its matching Vex CPU module, RAM sources, ROM data, and an `rtl_sources.txt` compiler-source manifest.

```sh
PYTHONHASHSEED=0 python3 chapters/05-memory-map/run.py
```

The normal firmware checks the first and final ROM words, first and final SRAM words, and register readback before writing completion. The negative firmware loads from unmapped address `0x30000000`. Inspect `results/05/memory_map.csv`, `results/05/run.log`, and the corresponding output under `results/05-unmapped/`.

An endpoint ACK is registered so its response is aligned with the selected transaction. ACK means the request has completed; data that happens to be visible on a bus without an ACK is not a completed read.

## What does a PASS prove?

The map unit test proves that the declared regions are aligned, non-overlapping, and selected at their boundaries. The normal CPU run proves accesses reached the intended targets. The unmapped test proves a hole receives no response and cannot produce a false completion. Stage 06 then asks LiteX to generate the SoC map and checks the firmware contract against it.
