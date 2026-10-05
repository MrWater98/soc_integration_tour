# 02 — Wishbone Requests, Responses, and Failure Capture

Here the CPU is temporarily removed. A deterministic Migen test master talks to one 32-bit register slave at byte address `0x1000` (Wishbone word address `0x400`). Removing the CPU makes it possible to control the request and deliberately create bad response timing.

```text
test master ── cyc/stb, adr, we, sel, dat_w ──> register slave
            <──────────── ack, err, dat_r ─────
```

## Which LiteX and Migen interfaces are used here?

This chapter does not create a `SoCCore`. It uses LiteX's `wishbone.Interface` to describe the slave port, then Migen's `Module`, `Signal`, `comb`, and `sync` to implement the register behavior. The Python generator in `verify.py` is the test master: it drives the same bus signals cycle by cycle. `run_simulation` runs the master and slave together. This isolates the Wishbone response rules before an interface like this is attached to a full SoC.

`RegisterSlave` combines `data_width=32`, `address_width=32`, and `addressing="word"`: each transfer carries 32 bits, and `adr` counts words rather than bytes, so byte address `0x1000` is `adr=0x400`. The four `sel` bits independently enable the four bytes. Changing `addressing` to `"byte"` without changing the test address would access a different location; changing the data width to 64 bits would also require widening the byte select and data mask.

`wait_cycles` controls how long the state machine stays in `WAIT`; it changes response latency, not the address. `fault` deliberately makes ACK early, holds it too long, or never asserts it. With `no_ack`, the master still holds `cyc/stb`, so the test's wait limit is necessary to stop the check instead of waiting forever.

The values `wait_cycles=2`, `max_wait=6` in the negative cases, register address `0x1000`, and data patterns such as `0xaabbccdd` are test parameters. Six cycles is the checker's timeout bound, not a Wishbone response limit; changing it changes when the test declares a timeout, not how the protocol works. The word-address conversion depends on the configured 32-bit, word-addressed interface: if its width or addressing mode changes, update the address and byte-lane checks together.

## Read one transaction

The master asserts `cyc` and `stb`, sets the address and operation, and holds the request fields stable until completion. A read has `we=0`; a write has `we=1`. On a read, `dat_r` is consumed when `ack` completes the transaction. `sel` selects byte lanes; `sel=0001` changes only the lowest byte of a 32-bit word.

```text
             request       wait       response       idle
cyc/stb         1/1          1/1          1/1           0/0
ack               0            0            1             0
```

The initial register value is `0x11223344`. Seeing that value on `dat_r` while `ack=0` is not yet a completed read. The master only accepts the value on the response cycle.

## Questions and answers

### What does each signal mean here?

| Signal | Meaning in this test |
| --- | --- |
| `cyc`, `stb` | A transaction is active and the current request is valid |
| `adr` | Wishbone word address; `0x400` represents byte address `0x1000` |
| `we` | `0` reads, `1` writes |
| `dat_w`, `dat_r` | Write data toward the slave; read data back from it |
| `sel` | Four byte enables for the 32-bit data word |
| `ack` | The slave has completed this request |
| `err` | Error response; this test expects it to remain low |

### How did we capture the failure instead of just seeing a failed run?

The test checks protocol conditions at specific points and records every cycle to CSV and VCD. Before it starts a request, it requires ACK to be low. While requesting, it waits cycle by cycle up to a fixed limit. After ACK, it withdraws `cyc/stb` and requires ACK to return low. Those observations identify whether the problem occurred before, during, or after a transaction.

| Injected case | What the checker samples | How it identifies the fault |
| --- | --- | --- |
| `no_ack` | Correct address `0x400`, request remains active, ACK sampled every cycle | `max_wait=6` is exceeded; because the checker increments before comparing, it reports seven counted wait cycles and raises a timeout |
| `unmapped` | Request uses word address `0x401`, outside this slave's one-word decode | The trace shows the wrong address and no ACK; timeout is attributed to the unimplemented address |
| `early_ack` | ACK before the master asserts a request | The pre-request check sees ACK high while the bus is idle and raises a protocol error immediately |
| `held_ack` | ACK after master deasserts `cyc/stb` | The post-response check sees ACK still high on an idle bus and raises a protocol error |
| `wait2` | ACK timing for an otherwise valid request | The trace contains two additional wait cycles before the single ACK |

This is why the test has both a transaction checker and a passive cycle recorder. The checker decides pass/fail; the CSV/VCD preserves the evidence that explains that decision. A timeout alone would not distinguish an absent target from a target that saw the request but failed to respond; the recorded address and handshake signals do.

The exact timeout number is a checker setting: `max_wait=6` means “allow six counted waits, then fail when the count becomes 7.” It is not a bus timing rule. The same bound is used for the unmapped-address case so both missing-response traces terminate predictably.

### Why ACK must belong to the active request?

The master interprets ACK as “this transaction is complete.” An ACK while idle can be mistaken for a response to a later request. An ACK held after completion can make one request look like multiple completions. Requiring a fresh, single response cycle tied to an active `cyc/stb` avoids stale or duplicate responses.

### What do the byte-lane tests verify?

The test first writes `0xaabbccdd`, then writes each lane separately and reads the register back. Each `sel` bit controls one byte. A final `sel=0` write must leave the value unchanged. These checks catch a slave that ignores the byte enables or updates the wrong byte.

## Run and inspect

```sh
python3 chapters/02-wishbone/verify.py
python3 chapters/02-wishbone/verify.py --case wait2
```

The default run covers normal read/write/readback, byte enables, zero select, two wait cycles, missing ACK, early ACK, held ACK, and an unmapped address. It writes `results/02/<case>.csv` and `.vcd`. Start with `normal.csv`: find `cyc=stb=1`, follow the same address until `ack=1`, then check that request and ACK return low. The CSV is readable without a waveform viewer; the VCD can be opened with GTKWave.

## What does a PASS prove?

The normal-case PASS proves the register slave returns and stores the expected values under the tested timing and byte-enable rules. A negative-case PASS means the named protocol violation was detected. It does not prove that every Wishbone feature (bursts, multiple masters, or arbitration) is implemented; this is a single-master, single-slave Classic transaction model.
