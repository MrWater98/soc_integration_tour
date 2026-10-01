# 01 — VexiiRiscv Reset and First Store

## Integration change

Instantiate LiteX's native `vexiiriscv/standard` CPU with a 64-byte initialized ROM and a memory-mapped write endpoint at byte address `0x40`. The program executes `addi x1,x0,64` followed by `sw x1,0(x1)`.

```text
VexiiRiscv AXI-Lite pBus (byte addresses)
                │
                ▼  LiteX native AXILite2Wishbone
       32-bit Wishbone (word addresses)
          ├── ROM       0x00000000–0x0000003f
          └── endpoint  0x00000040–0x0000007f
```

LiteX creates the bus adapter while registering the CPU master. The stage configures the CPU and Wishbone endpoint; it does not implement the adapter.

## Run and acceptance

```sh
PYTHONHASHSEED=0 python3 chapters/01-cpu-bringup/run.py
python3 chapters/01-cpu-bringup/tiny_bus.py
```

The native CPU runs twice. The nominal case must log the reset fetch at `0x0` and a write of `0x40` to byte address `0x40`. The negative case holds ACK low and must observe the pending write without reporting a normal write completion. The tiny bus model is a separate endpoint timing check; it does not replace CPU simulation.

Generated evidence is under `results/01/` and `results/01-no-ack/`: build/compile/run logs, generated maps, and VCD traces.

## Interface constraints

- CPU-side addresses are byte addresses; the 32-bit word-addressed Wishbone endpoint sees `0x40 / 4 = 0x10`.
- A Wishbone request is active while `cyc` and `stb` are high; the access completes only on the target's ACK.
- Prefetch can produce multiple ROM reads. The fetch marker reports an observed bus request, while the endpoint write proves the firmware reached its store.

Stage 02 uses a dedicated controllable master to qualify the slave-side response behavior.
