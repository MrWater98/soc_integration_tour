#!/usr/bin/env python3
"""Reproducible, coverage-directed Chapter 13 system regression."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import random
import re
import subprocess
import time

from run import (CHAPTER, ROOT, Config, add_litex_to_path, compile_firmware,
                 verify_case, workload_sequence)
from litex_builder import elaborate, compile_simulator, run_simulator, sha256


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


# Named functional requirements. RTL code coverage has a separate denominator.
TARGETS = {
    "boot.complete", "fault.rom", "fault.csr", "fault.irq", "stress.long",
    "reset.uart.early", "reset.uart.late", "reset.bus.early", "reset.bus.late",
    "reset.irq", "reset.concurrent", "reset.repeated", "reset.short", "reset.long",
    "bus.short_wait", "bus.long_wait", "irq.concurrent", "protocol.i2c_nack",
    "memory.first_last", "memory.scoreboard",
} | {f"operation.{op}" for op in range(4)} | {
    f"transition.{a}.{b}" for a in range(4) for b in range(4)
} | {f"memory.byte_lane.{lane}" for lane in range(4)}


def memory_scoreboard(log, initial_words=None):
    """Compare actual slave reads against preceding byte-selected bus writes."""
    words, lanes, checked = dict(initial_words or {}), set(), 0
    pattern = r"MEMORY_TRANSACTION adr=0x([0-9a-f]+) we=(\d) sel=([0-9a-f]+) write=0x([0-9a-f]+) read=0x([0-9a-f]+)"
    for match in re.finditer(pattern, log):
        address, write, select, value, received = (int(x, 16) for x in match.groups())
        if write:
            if select == 15: words[address] = value
            elif address in words:
                mask = sum(255 << (8 * lane) for lane in range(4) if select & (1 << lane))
                words[address] = (words[address] & ~mask) | (value & mask)
                if select in (1, 2, 4, 8): lanes.add(select.bit_length() - 1)
        elif address in words:
            if received != words[address]:
                raise AssertionError(f"SRAM scoreboard word 0x{address:x}: 0x{received:x} != 0x{words[address]:x}")
            checked += 1
    return lanes, checked


def observe(log, case, cfg):
    hits = set()
    error = case["expected_fail"]
    if error:
        hits.add({0xe1: "fault.rom", 0xe3: "fault.csr", 0xe5: "fault.irq"}[error])
        return hits
    hits.add("boot.complete")
    recovery = log.rsplit("RESET_RELEASE", 1)[-1] if case["reset_mode"] else log
    initial = {cfg.regions["sram"][0] // 4 + i: (0x01020304 ^ (i * 0x1021)) & 0xffffffff
               for i in range(cfg.sram_size // 4)}
    initial[cfg.regions["sram"][0] // 4] = 0xbbccaa44
    lanes, checked = memory_scoreboard(recovery, initial)
    expected_writes = []
    for value in workload_sequence(case["seed"], case["count"]):
        if value & 3 != 3: continue
        address = cfg.regions["sram"][0] // 4 + (value >> 2) % (cfg.sram_size // 4)
        lane = (value >> 16) & 3
        expected_writes += [(address, 15, value),
                            (address, 1 << lane, (value >> 24) << (8*lane))]
    actual_writes = []
    for match in re.finditer(r"MEMORY_TRANSACTION adr=0x([0-9a-f]+) we=1 sel=([0-9a-f]+) write=0x([0-9a-f]+)", recovery):
        address, select, data = (int(item, 16) for item in match.groups())
        mask = sum(255 << (8*lane) for lane in range(4) if select & (1 << lane))
        actual_writes.append((address, select, data & mask))
    if actual_writes != expected_writes: raise AssertionError("SRAM bus write sequence differs from seeded workload")
    if checked: hits.add("memory.scoreboard")
    hits |= {f"memory.byte_lane.{lane}" for lane in lanes}
    operations = [int(value, 16) & 3 for value in re.findall(r"STRESS_OP encoded=0x([0-9a-f]+)", recovery)]
    hits |= {f"operation.{op}" for op in operations}
    hits |= {f"transition.{a}.{b}" for a, b in zip(operations, operations[1:])}
    if case["count"] >= case["long_threshold"]: hits.add("stress.long")
    if "I2C_ADDRESS" in recovery and "ack=0" in recovery: hits.add("protocol.i2c_nack")
    if all(f"MEMORY_BOUNDARY name={region}" in recovery for region in ("sram", "main_ram")):
        hits.add("memory.first_last")
    if re.search(r"TIMER_ISR count=\d+ op=\d+ stage=7", recovery): hits.add("irq.concurrent")
    hits.add("bus.short_wait" if case["bus_delay"] <= 8 else "bus.long_wait")
    mode = case["reset_mode"]
    if mode:
        assertions = [line for line in log.splitlines() if line.startswith("RESET_ASSERT")]
        for line in assertions:
            if f"mode={mode}" not in line: raise AssertionError("reset trigger mode mismatch")
            if mode == 2 and "bus_wait=1" not in line: raise AssertionError("bus reset missed the wait")
            if mode == 3 and "irq=1" not in line: raise AssertionError("IRQ reset missed the asserted line")
            stage = int(re.search(r"stage=(\d+)", line).group(1))
            if stage < case["reset_stage"]: raise AssertionError("reset occurred before selected phase")
            if stage == 7: hits.add("reset.concurrent")
        hits.add("reset.short" if case["reset_width"] <= 4 else "reset.long")
        if case["reset_count"] > 1: hits.add("reset.repeated")
        if mode == 3: hits.add("reset.irq")
        elif mode == 1:
            hits.add("reset.uart.early" if case["delay"] < cfg.bit_cycles else "reset.uart.late")
        else:
            hits.add("reset.bus.early" if case["delay"] < case["bus_delay"] // 2 else "reset.bus.late")
    return hits


def plan_case(rng, index, missing, args, cfg):
    """Direct uncovered scenario bins, randomize everything within their constraints."""
    focus = next((name for name in (
        "fault.rom", "fault.csr", "fault.irq", "reset.uart.early", "reset.uart.late",
        "reset.bus.early", "reset.bus.late", "reset.irq", "reset.concurrent", "reset.repeated",
        "reset.short", "reset.long", "bus.long_wait", "stress.long") if name in missing), "random")
    mode = {"reset.uart.early": 1, "reset.uart.late": 1, "reset.bus.early": 2,
            "reset.bus.late": 2, "reset.irq": 3, "reset.concurrent": 1,
            "reset.repeated": 2, "reset.short": 1, "reset.long": 1}.get(focus, 0)
    if focus == "random": mode = rng.choice((0, 0, 1, 2, 3))
    bus_delay = rng.choice((4, 8, 17, 31))
    if focus == "reset.bus.late" and bus_delay < 8: bus_delay = 8
    if focus == "bus.long_wait": bus_delay = rng.choice((17, 31))
    count = args.long_iterations if focus == "stress.long" else rng.randint(args.iterations, 2 * args.iterations)
    seed = rng.randrange(1, 2**32)
    width = rng.choice((2, 4, 8, 16))
    if focus == "reset.short": width = 2
    if focus == "reset.long": width = 16
    delay = 0
    if mode == 1:
        delay = rng.randrange(1, 4 * cfg.bit_cycles - 1)
        if focus == "reset.uart.early": delay = rng.randrange(1, cfg.bit_cycles)
        if focus == "reset.uart.late": delay = rng.randrange(cfg.bit_cycles, 4*cfg.bit_cycles-1)
    if mode == 2:
        delay = rng.randrange(bus_delay - 2)
        if focus == "reset.bus.early": delay = 0
        if focus == "reset.bus.late": delay = bus_delay - 3
    stage = 7 if focus == "reset.concurrent" else rng.choice((0, 3, 7))
    # The one-shot timer cannot fire before stage 4; stage 7 selects periodic IRQ.
    if mode == 3 and stage == 3: stage = 4
    resets = rng.choice((1, 2, 3)) if mode else 1
    if focus == "reset.repeated": resets = 3
    fault = {"fault.rom": 0, "fault.csr": 1, "fault.irq": 2}.get(focus, 0)
    expected = {"fault.rom": 0xe1, "fault.csr": 0xe3, "fault.irq": 0xe5}.get(focus)
    case = dict(name=f"case-{index:04d}", focus=focus, seed=seed, count=count,
                timer=rng.choice((8000, 12000, 20000)), bus_delay=bus_delay,
                reset_mode=mode, delay=delay, reset_stage=stage, reset_width=width,
                reset_count=resets, expected_fail=expected, corrupt_rom=focus == "fault.rom",
                long_threshold=args.long_iterations)
    case["arguments"] = [f"+workload_seed={seed}", f"+seed={seed}", f"+stress_count={count}",
                         f"+timer_cycles={case['timer']}", f"+bus_delay={bus_delay}", f"+fault={fault}",
                         f"+reset_mode={mode}", f"+reset_delay={delay}", f"+reset_stage={stage}",
                         f"+reset_count={resets}", f"+reset_width={width}"]
    return case


def code_coverage(result):
    files = sorted((result / "cases").glob("*.cov"))
    if not files: raise RuntimeError("coverage-enabled simulator produced no .cov file")
    out = result / "coverage"
    out.mkdir(exist_ok=True)
    commands = [
        ["verilator_coverage", "--write", str(out / "merged.dat"), *map(str, files)],
        ["verilator_coverage", "--write-info", str(out / "merged.info"), str(out / "merged.dat")],
        ["verilator_coverage", "--annotate", str(out / "annotated"), "--annotate-min", "1", str(out / "merged.dat")],
    ]
    with (out / "tool.log").open("w") as stream:
        for command in commands:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=60)
    # Preserve tool output; report hit counters by type and file, not a single blended percentage.
    stats = {}
    for line in (out / "merged.dat").read_text().splitlines():
        if not line.startswith("C '"): continue
        metadata, count = line[3:].rsplit("' ", 1)
        fields = dict(re.findall(r"\x01([^\x02]+)\x02([^\x01]*)", metadata))
        category = fields.get("page", "unknown").split("/")[0]
        key = f"{Path(fields.get('f', 'unknown')).name}:{category}"
        row = stats.setdefault(key, {"points": 0, "hit": 0})
        row["points"] += 1
        row["hit"] += int(int(count) > 0)
    for row in stats.values(): row["percent"] = round(100 * row["hit"] / row["points"], 2)
    save(out / "code-summary.json", stats)
    return stats


def execute(result, case, cfg, manifest, timeout, trace):
    start = time.monotonic()
    log = run_simulator(result, case["name"], case["arguments"], manifest=manifest,
                        corrupt_rom=case["corrupt_rom"], timeout=timeout, require_wave=trace)
    cov = result / "cases" / f"{case['name']}.cov"
    if not cov.exists() or not cov.stat().st_size: raise AssertionError("missing per-case RTL coverage evidence")
    runtime = replace(cfg, stress_bytes=case["count"], timer_period=case["timer"])
    serial = verify_case(log, runtime, name=case["name"], expected_fail=case["expected_fail"],
                         reset_mode=case["reset_mode"], reset_count=case["reset_count"], workload_seed=case["seed"])
    (result / "cases" / f"{case['name']}.uart.txt").write_text(serial)
    cycle_match = re.search(r"SIM_CYCLES count=(\d+)", log)
    if not cycle_match: raise AssertionError("missing actual simulation cycle count")
    hits = observe(log, case, cfg)
    return dict(case=case["name"], status="PASS", focus=case["focus"],
                cycles=int(cycle_match.group(1)), seconds=round(time.monotonic()-start, 3),
                hits=sorted(hits))


def main():
    parser = argparse.ArgumentParser(description="第 13 章可复现、覆盖率驱动的整机压力回归")
    parser.add_argument("--output", type=Path, default=ROOT / "results/13-campaign")
    parser.add_argument("--seed", type=int, default=1301, help="campaign seed, recorded in every report")
    parser.add_argument("--cases", type=int, default=16, help="minimum runs, excluding targeted closure runs")
    parser.add_argument("--max-cases", type=int, default=32, help="hard limit on runs including closure")
    parser.add_argument("--iterations", type=int, default=256, help="lower random iteration bound")
    parser.add_argument("--long-iterations", type=int, default=4096, help="long-case iterations and functional bin threshold")
    parser.add_argument("--min-cycles", type=int, default=2_000_000, help="minimum sum of actually executed clocks")
    parser.add_argument("--max-cycles", type=int, default=100_000_000, help="watchdog clocks per case")
    parser.add_argument("--timeout", type=float, default=600, help="wall seconds per case")
    parser.add_argument("--trace", action="store_true", help="save FST for every case; usually expensive")
    parser.add_argument("--reuse-build", action="store_true", help="reuse only when source/config fingerprints match")
    parser.add_argument("--replay", type=Path, help="replay one cases/*.plan.json from a failed run")
    for name in ("gpio_width", "rom_size", "sram_size", "main_ram_size", "stack_size",
                 "uart_fifo_depth", "sys_clk_hz", "baud"):
        parser.add_argument("--" + name.replace("_", "-"), type=lambda value: int(value, 0))
    args = parser.parse_args()
    if not (0 < args.cases <= args.max_cases and 0 < args.iterations < args.long_iterations and args.timeout > 0 and args.min_cycles >= 0):
        parser.error("require 0 < cases <= max-cases, 0 < iterations < long-iterations, timeout > 0, min-cycles >= 0")
    cfg = Config(max_cycles=args.max_cycles, **{name: getattr(args, name) for name in Config.__dataclass_fields__
        if name != "max_cycles" and hasattr(args, name) and getattr(args, name) is not None}).validate()
    result = args.output.resolve()
    result.mkdir(parents=True, exist_ok=True)
    if not args.replay and (result / "cases").exists() and any((result / "cases").iterdir()):
        parser.error("output already has cases; choose a fresh --output (previous evidence retained)")
    manifest_path = result / "campaign-build.json"
    fingerprint = dict(config=cfg.values, source_sha256={p.name: sha256(p) for p in CHAPTER.iterdir()
        if p.suffix in (".py", ".c", ".v", ".S") and not p.name.startswith("test_")}, trace=args.trace)
    add_litex_to_path(ROOT)
    from soc import TutorialSoC
    binary = result / "builder/gateware/obj_dir/Vsim"
    if args.reuse_build:
        if not binary.exists() or not manifest_path.exists(): parser.error("no prior campaign build")
        manifest = json.loads(manifest_path.read_text())
        if manifest["fingerprint"] != fingerprint or manifest["binary_sha256"] != sha256(binary):
            parser.error("source/config/binary changed: rebuild without --reuse-build in a fresh output")
        for source in manifest["rtl_sources"]:
            origin = Path(source["origin"])
            if not origin.is_file() or sha256(origin) != source["source_sha256"]:
                parser.error(f"generated HDL or dependency changed: {origin}")
        if sha256(result / "firmware/program.bin") != manifest["firmware_sha256"] or sha256(result / "builder/gateware/sim_rom.init") != manifest["rom_sha256"]:
            parser.error("firmware or ROM changed; rebuild in a fresh output")
    else:
        print("BUILD campaign: RTL coverage enabled", flush=True)
        elaborate(result, cfg, TutorialSoC, rom_words=[0x0000006f])
        words = compile_firmware(result, cfg)
        elaborate(result, cfg, TutorialSoC, rom_words=words, emit_rtl=True, coverage=True, trace=args.trace)
        compile_simulator(result)
        manifest = dict(fingerprint=fingerprint, binary_sha256=sha256(binary),
                        firmware_sha256=sha256(result / "firmware/program.bin"),
                        rom_sha256=sha256(result / "builder/gateware/sim_rom.init"),
                        rtl_sources=json.loads((result / "rtl/sources.json").read_text()),
                        verilator=subprocess.check_output(["verilator", "--version"], text=True).strip())
        save(manifest_path, manifest)
    if args.replay:
        case = json.loads(args.replay.read_text())
        case["name"] += f"-replay-{time.time_ns()}"
        save(result / "cases" / f"{case['name']}.plan.json", case)
        row = execute(result, case, cfg, manifest, args.timeout, args.trace)
        save(result / "replay-summary.json", row)
        if not args.trace: print("Waveforms disabled; rebuild replay in a new --output with --trace if needed.")
        print(f"REPLAY PASS {case['name']}: {row['cycles']} clocks")
        return
    cases_dir = result / "cases"
    # Old coverage cannot contribute to the new run's denominator or pass result.
    if cases_dir.exists():
        if any(cases_dir.iterdir()):
            parser.error("output already has cases; choose a fresh --output or use --replay (previous evidence retained)")
    cases_dir.mkdir(exist_ok=True)
    rng = random.Random(args.seed)
    hits, witnesses, rows = set(), {}, []
    actual_cycles = 0
    save(result / "campaign-config.json", vars(args) | {"output": str(result), "replay": None})
    try:
        for index in range(args.max_cases):
            if index >= args.cases and not (TARGETS-hits) and actual_cycles >= args.min_cycles: break
            case = plan_case(rng, index, TARGETS-hits, args, cfg)
            save(cases_dir / f"{case['name']}.plan.json", case)
            row = execute(result, case, cfg, manifest, args.timeout, args.trace)
            rows.append(row)
            hits.update(row["hits"])
            for hit in row["hits"]: witnesses.setdefault(hit, []).append(case["name"])
            actual_cycles += row["cycles"]
            print(f"PASS {case['name']} focus={case['focus']} cycles={row['cycles']} coverage={len(hits & TARGETS)}/{len(TARGETS)}", flush=True)
            save(result / "progress.json", dict(rows=rows, actual_cycles=actual_cycles, uncovered=sorted(TARGETS-hits)))
    except Exception as exc:
        save(result / "failure.json", dict(case=case, error=str(exc), completed=rows,
             replay=f"python {CHAPTER/'campaign.py'} --output {result} --max-cycles {cfg.max_cycles} --reuse-build --replay {cases_dir / (case['name']+'.plan.json')}" + (" --trace" if args.trace else "")))
        print(f"FAIL {case['name']}: {exc}; see {result/'failure.json'}", flush=True)
        raise
    summary = dict(status="PASS" if not TARGETS-hits and actual_cycles >= args.min_cycles else "INCOMPLETE",
                   seed=args.seed, actual_cycles=actual_cycles, minimum_cycles=args.min_cycles, cases=rows,
                   functional=dict(hit=len(hits & TARGETS), total=len(TARGETS), uncovered=sorted(TARGETS-hits), witnesses=witnesses),
                   code_coverage=code_coverage(result))
    save(result / "campaign-summary.json", summary)
    report = ["# Chapter 13 压力回归结果", "", f"状态：{summary['status']}；种子：{args.seed}",
              f"实际运行 {actual_cycles:,} 个时钟；{len(rows)} 个场景；功能覆盖 {len(hits & TARGETS)}/{len(TARGETS)}。", "",
              "功能覆盖是本工具定义的场景清单；RTL 覆盖单独统计，保留未命中点。", "", "## 未命中功能点", "",
              *(sorted(TARGETS-hits) or ["无"]), "", "## RTL 覆盖", "", "| 文件 / 类型 | 命中 / 总数 | 比例 |", "| --- | --- | --- |"]
    report.extend(f"| {key} | {row['hit']} / {row['points']} | {row['percent']}% |" for key,row in summary["code_coverage"].items())
    (result / "REPORT.md").write_text("\n".join(report)+"\n")
    print(f"{summary['status']} campaign: {actual_cycles} clocks, {len(rows)} cases, {len(hits & TARGETS)}/{len(TARGETS)} functional bins")
    if summary["status"] != "PASS": raise SystemExit(2)


if __name__ == "__main__": main()
