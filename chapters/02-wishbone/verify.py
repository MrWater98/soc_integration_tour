#!/usr/bin/env python3
"""Run normal, boundary, and intentionally broken Wishbone transactions."""

import argparse
import csv
from pathlib import Path
import sys


CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path

add_litex_to_path(ROOT)

from migen import run_simulation
from migen.fhdl import verilog
from migen.sim import passive
from register import RegisterSlave, WORD_ADDRESS


class ProtocolError(AssertionError):
    pass


def transaction(bus, *, address=WORD_ADDRESS, write=False, data=0, sel=0xF, max_wait=12):
    if (yield bus.ack):
        raise ProtocolError("ACK was already high before the request")
    yield bus.adr.eq(address)
    yield bus.we.eq(int(write))
    yield bus.dat_w.eq(data)
    yield bus.sel.eq(sel)
    yield bus.cyc.eq(1)
    yield bus.stb.eq(1)
    yield
    waited = 0
    while not (yield bus.ack):
        waited += 1
        if waited > max_wait:
            raise TimeoutError(f"word address 0x{address:x} waited {waited} cycles without ACK")
        yield
    read_value = (yield bus.dat_r)
    if (yield bus.err):
        raise ProtocolError("Slave asserted ERR")
    yield bus.cyc.eq(0)
    yield bus.stb.eq(0)
    yield
    if (yield bus.ack):
        raise ProtocolError("ACK remained high after the request")
    yield
    return read_value, waited


def expect_exception(task, kind, marker):
    try:
        yield from task
    except kind as exc:
        print(f"PASS {marker}: {exc}")
        return
    raise AssertionError(f"FAIL {marker}: Fault was not detected")


def make_master(dut, case):
    bus = dut.bus
    if case in ("normal", "wait2"):
        value, wait = yield from transaction(bus)
        assert value == 0x11223344, f"Reset value mismatch: {value:08x}"
        if case == "wait2":
            assert wait >= 3, f"Wait-cycle setting did not take effect: {wait}"
        yield from transaction(bus, write=True, data=0xAABBCCDD)
        value, _ = yield from transaction(bus)
        assert value == 0xAABBCCDD
        expected = value
        for byte_index in range(4):
            lane = 1 << byte_index
            replacement = (0x10 + byte_index) << (8 * byte_index)
            yield from transaction(bus, write=True, data=replacement, sel=lane)
            expected = (expected & ~(0xFF << (8 * byte_index))) | replacement
            actual, _ = yield from transaction(bus)
            assert actual == expected, f"sel={lane:04b}: expected {expected:08x}, got {actual:08x}"
        yield from transaction(bus, write=True, data=0, sel=0)
        actual, _ = yield from transaction(bus)
        assert actual == expected, "sel=0 must not modify the register"
        print(f"PASS 02-{case.upper()}: initial, full-word, byte-lane and zero-select checks; final=0x{actual:08x}")
    elif case == "no_ack":
        yield from expect_exception(transaction(bus, max_wait=6), TimeoutError, "02-NO-ACK")
    elif case == "early_ack":
        yield from expect_exception(transaction(bus), ProtocolError, "02-EARLY-ACK")
    elif case == "held_ack":
        yield from expect_exception(transaction(bus), ProtocolError, "02-HELD-ACK")
    elif case == "unmapped":
        yield from expect_exception(transaction(bus, address=WORD_ADDRESS + 1, max_wait=6), TimeoutError, "02-UNMAPPED")


@passive
def capture(bus, rows):
    cycle = 0
    while True:
        rows.append({
            "cycle": cycle,
            "adr_word": (yield bus.adr),
            "cyc": (yield bus.cyc),
            "stb": (yield bus.stb),
            "we": (yield bus.we),
            "sel": (yield bus.sel),
            "dat_w": (yield bus.dat_w),
            "dat_r": (yield bus.dat_r),
            "ack": (yield bus.ack),
        })
        cycle += 1
        yield


def main():
    parser = argparse.ArgumentParser(description="Stage 02 Wishbone transaction verification")
    parser.add_argument("--case", choices=("all", "normal", "wait2", "no_ack", "early_ack", "held_ack", "unmapped"), default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "results/02")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    cases = ("normal", "wait2", "no_ack", "early_ack", "held_ack", "unmapped") if args.case == "all" else (args.case,)
    rtl_dir = out / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    for case in cases:
        fault = case if case in ("no_ack", "early_ack", "held_ack") else None
        dut = RegisterSlave(wait_cycles=2 if case == "wait2" else 0, fault=fault)
        if case != "unmapped":
            rtl_dut = RegisterSlave(wait_cycles=2 if case == "wait2" else 0, fault=fault)
            bus = rtl_dut.bus
            ios = {bus.adr, bus.dat_w, bus.dat_r, bus.sel, bus.cyc, bus.stb,
                   bus.we, bus.ack, bus.err, rtl_dut.value}
            (rtl_dir / f"02-{case}.v").write_text(
                str(verilog.convert(rtl_dut, ios=ios, name="wishbone_register_slave")))
        rows = []
        run_simulation(dut, [make_master(dut, case), capture(dut.bus, rows)], vcd_name=str(out / f"{case}.vcd"))
        active = [r for r in rows if r["cyc"] and r["stb"]]
        idle_acks = [r for r in rows if r["ack"] and not (r["cyc"] and r["stb"])]
        if case in ("normal", "wait2"):
            assert len(active) > 13 and sum(r["ack"] for r in active) == 13
            assert not idle_acks, "idle bus must not assert ACK"
        elif case in ("no_ack", "unmapped"):
            assert active and not any(r["ack"] for r in rows)
        elif case in ("early_ack", "held_ack"):
            assert idle_acks, "fault case did not expose the invalid idle ACK"
        with (out / f"{case}.csv").open("w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
    manifest = ["Standalone RTL snapshots for the Wishbone register slave:"]
    descriptions = {
        "normal": "RegisterSlave with immediate normal response.",
        "wait2": "RegisterSlave configured for two wait cycles.",
        "no_ack": "RegisterSlave configured never to assert ACK.",
        "early_ack": "RegisterSlave fault mode that asserts ACK while idle.",
        "held_ack": "RegisterSlave fault mode that keeps ACK asserted after completion.",
    }
    for name in ("normal", "wait2", "no_ack", "early_ack", "held_ack"):
        if (rtl_dir / f"02-{name}.v").is_file():
            manifest.append(f"02-{name}.v: {descriptions[name]}")
    manifest.extend([
        "The unmapped case uses 02-normal.v; verify.py changes the Python master address to an undecoded word.",
        "The test master and cycle recorder are Python generators in verify.py, not RTL modules.",
    ])
    (rtl_dir / "rtl_sources.txt").write_text("\n".join(manifest) + "\n")
    print(f"Output: {out}")


if __name__ == "__main__":
    main()
