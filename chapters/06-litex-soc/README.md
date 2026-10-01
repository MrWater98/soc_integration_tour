# 06 — LiteX SoCCore and Builder

## Integration change

Replace the hand-assembled SoC shell with LiteX `SoCCore` and `Builder`. LiteX now owns CPU registration, integrated ROM/SRAM, the CSR bridge, bus interconnect, generated maps and simulator project. A small Wishbone completion endpoint remains project-specific.

The firmware is rebuilt for the LiteX map:

| Region | Byte address | Size |
| --- | ---: | ---: |
| ROM | `0x00000000` | 4 KiB |
| SRAM | `0x10000000` | 4 KiB |
| Completion | `0x80000000` | 4 KiB |
| CSR | `0xf0000000` | 64 KiB |

## Automatic CPU bus adaptation

The chapter does not call `AXILite2Wishbone(...)` directly. The CPU exposes AXI-Lite pBus while the SoCCore main bus defaults to Wishbone. During CPU-master registration, LiteX's `add_master()` invokes `add_adapter()`; its protocol conversion table instantiates the native `AXILite2Wishbone` bridge.

```text
soc.py selects VexiiRiscv
    → SoCCore uses its default Wishbone main bus
    → CPU AXI-Lite pBus is registered as cpu_bus0
    → LiteX instantiates AXILite2Wishbone
    → ROM / SRAM / completion endpoint use Wishbone
```

The LiteX implementation is in `litex/soc/interconnect/axi/axi_lite_to_wishbone.py`. The generated build log should contain `cpu_bus0 Bus adapted from AXI-Lite 32-bit to Wishbone 32-bit`.

## Run and acceptance

```sh
PYTHONHASHSEED=0 python3 chapters/06-litex-soc/run.py
```

The runner assembles this stage's firmware, asks Builder to emit the simulation project and address files, checks the generated regions, compiles the simulator, and runs the CPU. The completion endpoint must log the expected last-word write. A stale-map check must reject the prior hand-written SRAM and completion addresses before simulation.

Outputs are written under `results/06/`: `csr.csv`, generated software files, `memory_map.csv`, stale-map evidence, build/compile/run logs and VCD.

## LiteX construction contract

- `soc.py` defines the SoCCore parameters and adds the completion endpoint.
- `vexii_config.py` selects the native VexiiRiscv standard variant with source updates disabled.
- `cpu_sim.py` assembles firmware and packs the ROM image.
- `litex_builder.py` runs Builder, checks the generated memory map and compiles/runs the simulator.
- The completion endpoint uses registered ACK. The CPU pass marker proves execution; generated maps alone prove only construction.

The software memory map changes from stage 05. Firmware must be rebuilt against each generated SoC map.
