# 02 — Wishbone Slave Contract

## Integration change

Run a Migen simulation with a deterministic Wishbone master and a single 32-bit register slave at byte address `0x1000` (word address `0x400`). The register starts at `0x11223344`; writes honor the four byte select lanes.

The checker captures each clock cycle to CSV and VCD. It tests reads, writes, readback, zero/two wait cycles, individual byte lanes, missing ACK, ACK while idle, ACK held after completion, and an address with no responding target.

## Run and acceptance

```sh
python3 chapters/02-wishbone/verify.py
python3 chapters/02-wishbone/verify.py --case wait2
```

The default run must print a PASS marker for each scenario and exit nonzero if a protocol assertion or timeout check fails. Outputs are written under `results/02/`.

## Interface constraints

| Signal | Direction | Contract |
| --- | --- | --- |
| `cyc`, `stb` | master → slave | Both high for an active request |
| `adr`, `we`, `sel`, `dat_w` | master → slave | Address, operation, byte lanes and write data stay stable until response |
| `dat_r`, `ack`, `err` | slave → master | Read data and completion/error response |

The 32-bit bus uses word addresses in this test: byte address `0x1000` maps to `adr=0x400`. ACK is accepted only for an active request and for one response cycle. The fault-injection modes exist only in this verification model.
