"""Compare Chapter 13 RTL on Verilator and a licensed event simulator."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
CHAPTER = Path(__file__).resolve().parent
STAGES = ("ROM", "RAM", "GPIO", "UART", "TIMER", "SPI", "I2C", "CONCURRENT")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(command, cwd, log, timeout):
    started = time.perf_counter()
    with log.open("w") as stream:
        try:
            proc = subprocess.run(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            return proc.returncode, time.perf_counter() - started
        except subprocess.TimeoutExpired:
            stream.write("\nBENCH13E_WALL_TIMEOUT\n")
            return 124, time.perf_counter() - started


def validate(log):
    if "SOC_COMPLETE data=0x0000005a" not in log or "SOC_FAIL" in log:
        raise ValueError("missing SoC completion or unexpected failure")
    values = [int(x) for x in re.findall(r"SELFTEST_STAGE id=\s*(\d+)", log)]
    if values != list(range(9)):
        raise ValueError(f"stage sequence differs: {values}")
    serial = bytes(int(x, 16) for x in re.findall(r"UART_TX_BYTE value=0x([0-9a-fA-F]+)", log)).decode("ascii")
    for index, stage in enumerate(STAGES, 1):
        if f"13-0{index} {stage} PASS\n" not in serial:
            raise ValueError(f"missing serial self-test {stage}")
    if "13 ALL PASS\n" not in serial:
        raise ValueError("missing serial completion")
    matches = re.findall(r"SIM_CYCLES count=(\d+)", log)
    if len(matches) != 1:
        raise ValueError("missing or repeated cycle count")
    return int(matches[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "results/13/rtl")
    parser.add_argument("--output", type=Path, default=ROOT / "results/13e")
    parser.add_argument("--commercial", choices=("vcs", "xrun"), default="vcs")
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be positive")
    source = args.input.resolve()
    out = args.output.resolve()
    if not (source / "sources.json").is_file():
        parser.error("Chapter 13 RTL snapshot is missing; run Chapter 13 first")
    records = json.loads((source / "sources.json").read_text())
    out.mkdir(parents=True, exist_ok=True)
    rtl = out / "rtl"
    rtl.mkdir(exist_ok=True)
    files = []
    hashes = {}
    for row in records:
        name = row["file"]
        if Path(name).name != name:
            raise ValueError(f"unsafe source name: {name}")
        path = source / name
        if digest(path) != row["snapshot_sha256"]:
            raise ValueError(f"RTL snapshot changed: {name}")
        shutil.copyfile(path, rtl / name)
        hashes[name] = digest(rtl / name)
        if name.endswith((".v", ".sv")):
            files.append(name)
    shutil.copyfile(CHAPTER / "bench13e.sv", rtl / "bench13e.sv")
    hashes["bench13e.sv"] = digest(rtl / "bench13e.sv")
    tools = ("verilator", args.commercial)
    summary = {"input": str(source), "source_sha256": hashes, "runs": args.runs,
               "host": os.uname().nodename, "results": {}}
    for tool in tools:
        executable = shutil.which(tool)
        if tool == "xrun" and executable:
            # Some modulefiles place a 32-bit launcher first, while the host
            # only has a 64-bit runtime loader.
            xrun64 = Path(executable).parent / "64bit/xrun"
            if xrun64.is_file():
                executable = str(xrun64)
        row = {"status": "SKIP"}
        summary["results"][tool] = row
        if executable is None:
            row["reason"] = "executable absent; load the corresponding module"
            continue
        version_flag = {"verilator": "--version", "vcs": "-ID", "xrun": "-version"}[tool]
        version = subprocess.run([executable, version_flag],
                                 capture_output=True, text=True, timeout=20)
        row["version"] = (version.stdout + version.stderr).strip().splitlines()[:3]
        work = out / tool
        work.mkdir(exist_ok=True)
        if tool == "verilator":
            command = [executable, "--binary", "--timing", "-j", "4", "-O2", "-Wno-fatal",
                       "--top-module", "bench13e", "--Mdir", str(work / "obj_dir"),
                       "bench13e.sv", *files]
            binary = work / "obj_dir/Vbench13e"
        elif tool == "vcs":
            command = [executable, "-full64", "-sverilog", "-timescale=1ns/1ps", "-q",
                       "-top", "bench13e", "-o", str(work / "simv"),
                       "bench13e.sv", *files]
            binary = work / "simv"
        else:
            command = [executable, "-64bit", "-sv", "-timescale", "1ns/1ps", "-top", "bench13e",
                       "-xmlibdirname", str(work / "xcelium.d"), "-elaborate", "bench13e.sv", *files]
            binary = None
        row["compile_command"] = command
        code, elapsed = call(command, rtl, work / "compile.log", 600)
        row.update(compile_exit=code, compile_seconds=elapsed)
        if code:
            row.update(status="FAIL", reason="compilation failed; inspect compile.log")
            continue
        durations, cycles = [], []
        for index in range(args.runs):
            run_command = ([str(binary)] if binary else
                           [executable, "-64bit", "-R", "-xmlibdirname", str(work / "xcelium.d")])
            path = work / f"run-{index+1}.log"
            code, elapsed = call(run_command, rtl, path, 180)
            if code:
                row.update(status="FAIL", reason=f"run {index+1} exited {code}")
                break
            try:
                cycles.append(validate(path.read_text(errors="replace")))
            except ValueError as exc:
                row.update(status="FAIL", reason=f"run {index+1}: {exc}")
                break
            durations.append(elapsed)
        else:
            row.update(status="PASS", run_seconds=durations, median_run_seconds=statistics.median(durations),
                       simulated_cycles=cycles)
    entries = summary["results"]
    if all(entries[t]["status"] == "PASS" for t in tools):
        a, b = entries[tools[0]], entries[tools[1]]
        if a["simulated_cycles"] == b["simulated_cycles"]:
            summary["commercial_over_verilator_run_time"] = b["median_run_seconds"] / a["median_run_seconds"]
        else:
            summary["cycle_mismatch"] = True
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({name: row["status"] for name, row in entries.items()}))
    print(f"Results: {out / 'summary.json'}")
    if any(row["status"] == "FAIL" for row in entries.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
