# 01 — Can VexRiscv Fetch and Store?

This is the first CPU-level experiment. It uses LiteX's native VexRiscv wrapper, a 64-byte initialized ROM, and a small memory-mapped write endpoint. The test is deliberately short so the log has only a few events to interpret.

```asm
addi x1, x0, 64   # x1 = 0x40
sw   x1, 0(x1)    # store 0x40 at byte address 0x40
```

## Start with the LiteX bus path

This diagram follows the generated [`sim.v`](../../results/01/rtl/sim.v). The CPU requests an access, the arbiter chooses its initiator, the decoder selects a device by address, and the device returns data and a response. All ranges below are **byte addresses**.

```text
                         VexRiscv / minimal
                        ┌────────┴────────┐
                        │                 │
                  iBus: fetch        dBus: load/store
                   interface0         interface1
                        └────────┬────────┘
                                 ▼
                      Arbiter + RoundRobin
                    select and hold a transaction
                                 ▼
                       shared Wishbone signals
                  adr / dat_w / sel / we / cyc / stb
                                 ▼
                              Decoder
                ┌────────────────┼──────────────────┐
                ▼                ▼                  ▼
               ROM           WriteTarget       Wishbone2CSR
           0x00–0x3f         0x40–0x7f       0xf0000000–0xf000ffff
           instructions    completion check         │ FSM
                │                │                  ▼
                │                │              CSR interface
                │                │           no CSR banks here
                └────────────────┼──────────────────┘
                                 ▼
                     response: dat_r / ack / err
                  ACK/ERR gated to the granted master
                                 ▼
                                CPU

Timeout watches a shared cyc & stb request waiting without ACK.
CRG supplies system clock/reset to CPU, interconnect, memory, endpoint, and bridge.
CPU externalInterruptArray is zero; this chapter has no interrupt source.
```

The `interface0/1` labels here are suffixes of the **CPU Wishbone signal names**. The CSR bridge uses another set of `interface0/1` names; read the full prefixes when following RTL. The ROM appears as `SRAM` in the hierarchy because LiteX uses its SRAM wrapper in read-only mode. This chapter has no writable SRAM.

### What do the management objects connect?

The tree at the start of `sim.v` is a module hierarchy. `bus`, `csr`, and `irq` are siblings under the SoC; actual signal connectivity is expressed in RTL.

| Name | Build-time task | Runtime hardware in this chapter |
| --- | --- | --- |
| `bus / SoCBusHandler` | Register masters, slaves, and address regions | Arbitration, decoding, response selection, and timeout logic. |
| `csr / SoCCSRHandler` | Allocate CSR pages/regions and register interfaces | A CSR bridge exists, but no GPIO/Timer CSR device is enabled. |
| `irq / SoCIRQHandler` | Allocate peripheral interrupt source indices | No sources; the CPU's 32-bit external interrupt vector stays zero. |
| `write_target / WriteTarget` | Add our Wishbone endpoint | Check address/data/byte lanes, generate ACK, and report simulation completion. |
| `csr_bridge / Wishbone2CSR` | Attach the CSR region to Wishbone | An FSM converts requests into CSR address, read/write enables, and data, then responds. |
| `csr_bankarray / CSRBankArray` | Collect peripheral CSRs and create banks | Empty here; CSR devices added later create their banks and interconnect. |
| `crg / CRG` | Establish clock/reset domains | System clock/reset signals. |

The later `registers / RegisterSlave` occupies the same bus position as `write_target`: a direct Wishbone slave. It stores and reads back a value. This chapter's `WriteTarget` checks completion writes and returns constant zero on reads. These endpoints are separate from CPU registers `x0–x31`.

### How does a request return to the CPU?

```text
Fetch: iBus requests a read at address 0
       → arbiter grants iBus → decoder selects ROM
       → ROM returns instruction data and ACK → ACK reaches iBus
       → CPU executes addi and obtains x1=0x40

Store: CPU executes sw and dBus requests a write
       byte address=0x40, Wishbone adr=0x10
       dat_w=0x40, we=1, sel=0xf, cyc=stb=1
       → arbiter grants dBus → decoder selects WriteTarget
       → endpoint accepts/checks the write and updates ACK
       → shared response reaches dBus, completing the access
```

The normal simulation calls `$display` and `$finish` when the endpoint accepts the expected write. Its log proves that the CPU issued the expected store; the simulation ends at that checkpoint before observing subsequent CPU execution after ACK.

Three concrete RTL anchors show routing:

```verilog
// Word address 0x10 corresponds to byte address 0x40.
decoder0[1] = (adr[29:4] == 1'd1);
// Shared payload/control, with CYC gated to the selected device.
assign projectsoc_writetarget_cyc = (cyc & decoder0[1]);
// Return ACK only to the granted CPU master.
assign projectsoc_vexriscv_interface1_ack =
    (ack & (roundrobin1 == 1'd1));
```

Selected read data is combined into shared `dat_r` and reaches both CPU interfaces. Only the granted interface receives ACK and accepts its transaction result. Arbitration chooses **who uses the bus**, decoding chooses **which device**, and the endpoint determines **when it completes**.

The timeout counter starts at `1_000_000`. At zero, this RTL forces `ack=1`, `dat_r=0xffffffff`, and an internal timeout flag; it does not assert `err` there. ACK alone therefore cannot prove a correct device response. The no-ACK experiment ends after 600 cycles, before bus timeout, and checks the outstanding request.

Later, a timer adds a separate interrupt path:

```text
CPU → Wishbone → CSR bridge → Timer registers: configure and clear pending
Timer → IRQ signal → CPU: request ISR entry
```

The IRQ handler allocates source indices at build time. Hardware signals notify the CPU at runtime; the ISR uses bus accesses to handle the event.

## First use of `SoCCore`: what do these parameters configure?

This chapter's `ProjectSoC` inherits from LiteX `SoCCore`. Calling `super().__init__(...)` asks LiteX to build the CPU, main bus, and integrated memories from the supplied parameters. The chapter then adds its own `WriteTarget` as the CPU store destination; `SoCCore` does not create this experiment-specific endpoint.

| Parameter | Value here | Why it is set this way |
| --- | --- | --- |
| `platform` | Simulation `SimPlatform` | Describes the simulated clock/pins, not a physical board. The runner adds a `CRG` for the `sys` clock domain. |
| `clk_freq` | `1_000_000` | Declares this simulation's system clock. It is a convenient experiment setting, not a VexRiscv requirement; keep the LiteX clock declaration and simulator clock consistent if you change it. |
| `cpu_type` | `"vexriscv"` | Selects LiteX's natively registered VexRiscv wrapper. |
| `cpu_variant` | `"minimal"` | Selects the pre-generated RV32I core without I/D caches. |
| `cpu_reset_address` | `0` | Sets the CPU reset vector. LiteX connects it to the pre-generated CPU’s `externalResetVector` input; CPU RTL uses that vector on reset. |
| `integrated_rom_size` | `0x40` (64 bytes) | Allocates only enough ROM for this short instruction sequence. SoCCore maps the ROM at the CPU reset address, zero. |
| `integrated_rom_init` | 16 machine-code words | Loads the `addi`, `sw`, stop loop, and NOP fill into ROM; it does not set the CPU reset location. |
| `integrated_sram_size` | `0` | No SRAM region is needed for this first CPU experiment. |
| `integrated_main_ram_size` | `0` | The program has no C runtime, stack, or writable data section, so it does not need main RAM yet. |
| `with_uart / with_timer / with_ctrl` | All `False` | Disables default UART, Timer, and control modules unused here, keeping the observed path small. |

`bus_standard` is not passed, so LiteX uses its default Wishbone main bus. `bus_arbiter="transaction"` keeps the current master selected until ACK/ERR completes its request, which suits the simultaneous instruction and data Wishbone masters.

### How does this chapter attach a custom block to LiteX?

`SoCCore` creates the common SoC structure; the project must register its own endpoint. `add_module("write_target", ...)` adds the Migen module to the design hierarchy, `bus.add_slave(...)` connects its Wishbone interface to LiteX's main bus, and `SoCRegion(origin=0x40, size=0x40, ...)` tells the decoder which addresses it answers. `SoCIORegion` also registers this low range as a CPU-visible I/O region. Creating a module without `add_slave` would leave CPU bus accesses disconnected from it.

The `0x40` endpoint base and `0x40`-byte region are choices for this tiny test. The program's `sw` address must land inside that region; if either changes, update the instruction/data expectation and the region together. Likewise, the 64-byte ROM size is derived from the chosen image depth and must still contain the reset instruction at address zero.

## How do these Python calls become RTL?

Python describes the hardware during the build; these are not functions the CPU calls at runtime. Consider the connection:

```python
self.add_module("write_target", WriteTarget())
self.bus.add_slave(
    name="write_target",
    slave=self.write_target.bus,
    region=SoCRegion(origin=0x40, size=0x40, mode="rw", cached=False),
)
```

`WriteTarget()` creates a Migen submodule, and `self.add_module` places it in the SoC hierarchy. `wishbone.Interface(...)` creates a bundle of signals such as `adr`, `dat_w`, `dat_r`, `sel`, `cyc`, `stb`, `we`, and `ack`; it does not define how ACK is generated. `slave=...bus` gives this bundle to LiteX's bus manager. `SoCRegion` supplies the decode rule: byte base `0x40`, 64-byte range, read/write access, and uncached behavior. During SoC elaboration, LiteX builds the address decoder, request routing, and response selection from this information.

This interface is word-addressed, so the generated Wishbone `adr` is a 30-bit word address: byte address `0x40` becomes `adr=0x10`. The generated RTL contains logic like this (generated names can vary by LiteX/Migen version):

```verilog
decoder0[1] = (adr[29:4] == 1'd1); // select byte addresses 0x40–0x7f
projectsoc_writetarget_cyc = cyc & decoder0[1];
projectsoc_writetarget_adr = adr;
projectsoc_writetarget_dat_w = dat_w;
```

The Migen statements inside `WriteTarget` become registers and combinational logic: `bus.dat_r.eq(0)` and `bus.err.eq(0)` become constant outputs; the ACK code under `self.sync` becomes clocked logic; Python `If` conditions become hardware comparisons and muxes. LiteX arbitrates the two Wishbone masters before address decoding. The decoder routes a matching request to its slave, and `ack/dat_r` return to the granted master over the shared bus.

After `run.py`, the complete RTL inputs for the two runs are in [`results/01/rtl`](../../results/01/rtl) and [`results/01-no-ack/rtl`](../../results/01-no-ack/rtl). Each contains the LiteX top-level `sim.v`, its `VexRiscv_Min.v` CPU definition, ROM initialization data, and an `rtl_sources.txt` manifest copied from the simulator's actual Verilog source list. The first top level shows the ACK response path; the second shows the endpoint configured never to respond. Running the chapter refreshes these files.

Read these settings as a group: the CPU reset vector is `0`, the integrated ROM also starts at `0`, and its initialized words must contain code for that location. The endpoint starts at `0x40`, immediately after the ROM range `0x00–0x3f`, so the regions do not overlap. `integrated_rom_size` is measured in bytes, while each item in `integrated_rom_init` is one 32-bit word; 16 words are exactly 64 bytes here. If the ROM is enlarged without moving the endpoint, the ROM claims address `0x40`; if only the reset address changes, the CPU fetches from a location that the current image was not linked for.

### Why does PC return to zero on reset?

`cpu_reset_address=0` is a build-time setting; Python does not write PC on every clock. LiteX calls the CPU wrapper's `set_reset_address(0)` and connects constant zero to the pre-generated core’s `externalResetVector` input. The CPU reset signal makes RTL reset PC to zero; after reset is released, the CPU fetches from address zero. SoCCore also maps the integrated ROM at the reset address, so ROM contents are available at zero.

```text
SoCCore: cpu_reset_address=0
       ├── VexRiscv RTL: reset PC ← 0
       └── integrated ROM: origin = 0
                                  │
CPU fetches from 0 after reset ───┘
```

The reset vector must match the ROM contents: firmware must be stored where the CPU begins fetching. This first experiment has no ELF `ENTRY` or linker script; the ROM is initialized directly through `integrated_rom_init`.

## Questions and answers

### Can caches be selected? Why are there two CPU buses?

LiteX provides several pre-generated VexRiscv variants. This chapter uses `minimal`, without caches or the M extension, to make memory accesses easy to follow. Instruction fetch and load/store still use two separate Wishbone masters: `ibus` fetches instructions and `dbus` performs data accesses.

```text
VexRiscv/minimal
  ibus (instruction) ─┐
                      ├─ LiteX transaction arbiter ─ decoder ─ ROM / SRAM / devices
  dbus (data) ────────┘
```

| `cpu_variant` | Instruction cache | Data cache | Typical use |
| --- | --- | --- | --- |
| `minimal` | No | No | RV32I teaching baseline |
| `lite` | Yes | No | Instruction cache with RV32IM |
| `standard` | Yes | Yes | General-purpose configuration |
| `linux` | Yes | Yes | Linux-class configuration |

The variants select LiteX-shipped VexRiscv RTL and matching compiler ISA flags. A variant name does not guarantee a particular area; use synthesis results for that.

Why set `bus_arbiter="transaction"`? `ibus` continuously fetches instructions, and `dbus` can request memory at the same time. A cycle-based grant can change ownership before a request and its response finish. Transaction arbitration holds the grant until ACK/ERR completes the transaction.

### Why start with only two instructions?

`addi` creates a known value, and `sw` turns it into an observable bus transaction. If the endpoint sees the expected address and data, the CPU left reset, fetched instructions, decoded and executed them, and issued a store. There is no C runtime, stack setup, or unrelated peripheral to obscure the first result.

### Does the first `FETCH` prove the instruction executed?

It proves that a read request at the ROM reset address completed. VexRiscv can prefetch, so a fetch log alone does not prove that a particular instruction retired. The endpoint's `0x40` write is stronger evidence: it can only happen after the program reaches the `sw`.

### Why does `0x40` become Wishbone address `0x10`?

The firmware and LiteX memory map use byte addresses. This 32-bit Wishbone endpoint is configured with word addressing, so one bus address step represents four bytes. Thus byte address `0x40` corresponds to Wishbone word address `0x40 / 4 = 0x10`. The stored value stays `0x40`; the conversion changes the address unit, not the data.

### Where is `Wishbone` in the Python files?

The CPU masters are Wishbone already. `cpu_bus0` and `cpu_bus1` connect the instruction and data ports; LiteX `SoCBusHandler` arbitrates requests, decodes addresses, and routes responses.

### What exactly does the no-ACK case show?

The endpoint is configured not to acknowledge the store. The CPU's request stays pending: the log records `DATA_WAIT` with byte address `0x40` and value `0x40`, then the bounded simulation times out. The test passes because it detects a live request that did not complete. It must not print the normal write-completion marker. This distinguishes “CPU issued a request” from “the target accepted the transaction.”

## Run and inspect

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

The first command runs the real CPU once with a responding endpoint and once with ACK suppressed. The second command is a small timing exercise for a toy bus endpoint; it is useful for understanding the handshake, but it is not a substitute for CPU simulation.

Look under `results/01/` and `results/01-no-ack/` for build logs, run logs, generated maps, and VCD traces. In a waveform, follow reset, the CPU `ibus` and `dbus`, the shared Wishbone request, and the endpoint `ack`. A request is active while `cyc` and `stb` are high. It completes only when the selected target responds.

## What does a PASS prove?

The normal PASS proves that VexRiscv fetched from reset and caused the endpoint to observe the expected store. `PASS 01-NO-ACK` proves that the test caught a request that never received ACK; it does not mean the store succeeded. Stage 02 isolates the slave response rules so each fault is easier to identify.
