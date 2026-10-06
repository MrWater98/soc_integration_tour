#!/usr/bin/env python3
"""Stage 00: check the pinned LiteX/VexRiscv simulation environment."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

LITEX_COMMIT = "aa32cc0d4952f0959afa0f8c16de2fd840128033"
PYTHONDATA_VEX_COMMIT = "642ecfed1c84460555d6d803d660cc60cfc1ecb6"
EXPECTED_PACKAGES = {
    "migen": "0.9.2",
    "pytest": "9.0.3",
    "pythondata-cpu-vexriscv": "1.0.1.post407",
    "pythondata-software-picolibc": "1.7.9.post181",
    "pythondata-software-compiler-rt": "0.0.post6206",
    "pythondata-misc-tapcfg": "0.0.post517",
}
CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path


def run(args, cwd=None, timeout=120):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description="Verify the SoC integration host environment")
    parser.add_argument("--strict", action="store_true", help="fail if any required check fails")
    parser.add_argument("--wishbone", action="store_true", help="run LiteX's Wishbone baseline test")
    parser.add_argument("--soc", action="store_true", help="check SoCCore/Builder dependencies")
    parser.add_argument("--require-tool", action="append", default=[], help="require another executable")
    parser.add_argument("--output", type=Path, default=Path("results/00/environment.json"))
    args = parser.parse_args()

    problems = []
    python_supported = (3, 10) <= sys.version_info[:2] < (3, 12)
    if not python_supported:
        problems.append(f"Python 3.10 or 3.11 is required; found {sys.version.split()[0]}")

    packages = {}
    for name in ("migen", "pytest", "pythondata-cpu-vexriscv"):
        try:
            packages[name] = importlib.metadata.version(name)
            expected = EXPECTED_PACKAGES[name]
            if packages[name] != expected:
                problems.append(f"{name}: expected {expected}, got {packages[name]}")
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
            problems.append(f"Missing Python package: {name}")

    soc_packages = {}
    if args.soc:
        for name in ("pythondata-software-picolibc", "pythondata-software-compiler-rt", "pythondata-misc-tapcfg"):
            try:
                soc_packages[name] = importlib.metadata.version(name)
                if soc_packages[name] != EXPECTED_PACKAGES[name]:
                    problems.append(f"{name}: expected {EXPECTED_PACKAGES[name]}, got {soc_packages[name]}")
            except importlib.metadata.PackageNotFoundError:
                soc_packages[name] = None
                problems.append(f"Missing SoCCore/Builder package: {name}")
        compiler = shutil.which("cc") or shutil.which("gcc")
        if not compiler:
            problems.append("A host C compiler is required for LiteX simulation")
        if compiler:
            probe = subprocess.run([compiler, "-E", "-x", "c", "-"], input="#include <json-c/json.h>\n",
                                   text=True, capture_output=True)
            if probe.returncode:
                problems.append("Missing json-c development header (install libjson-c-dev)")

    tools = {}
    required = ("verilator", "git", "riscv64-unknown-elf-gcc", "riscv64-unknown-elf-objcopy", *args.require_tool)
    for name in required:
        tools[name] = shutil.which(name)
        if not tools[name]:
            problems.append(f"Missing executable: {name}")

    vex_commit = None
    rtl_file = None
    root = add_litex_to_path(ROOT)
    try:
        import litex
        from litex import get_data_mod
        from litex.soc.cores.cpu import CPUS
        from litex.soc.cores.cpu.vexriscv.core import VexRiscv
        root = root or Path(litex.__file__).resolve().parents[1]
        if CPUS.get("vexriscv") is not VexRiscv:
            problems.append("LiteX CPU registry does not expose native vexriscv")
        rtl_dir = Path(get_data_mod("cpu", "vexriscv").data_location)
        rtl_file = rtl_dir / "VexRiscv_Min.v"
        if not rtl_file.is_file():
            problems.append(f"Missing minimal VexRiscv RTL: {rtl_file}")
        direct_url = importlib.metadata.distribution("pythondata-cpu-vexriscv").read_text("direct_url.json")
        if direct_url:
            vex_commit = json.loads(direct_url).get("vcs_info", {}).get("commit_id")
        if vex_commit and vex_commit != PYTHONDATA_VEX_COMMIT:
            problems.append(f"VexRiscv RTL commit mismatch: expected {PYTHONDATA_VEX_COMMIT}, got {vex_commit}")
    except Exception as exc:
        problems.append(f"LiteX/VexRiscv import failed: {exc}")

    verilator_version = None
    if tools.get("verilator"):
        verilator_version = run([tools["verilator"], "--version"]).stdout.strip()
        match = re.search(r"Verilator\s+(\d+)", verilator_version)
        if not match or int(match.group(1)) < 5:
            problems.append(f"Verilator 5 or newer is required; found {verilator_version}")

    rv32i_compiler = False
    gcc = tools.get("riscv64-unknown-elf-gcc")
    if gcc:
        probe = subprocess.run([gcc, "-march=rv32i2p0", "-mabi=ilp32", "-x", "c", "-fsyntax-only", "-"],
                               input="int main(void) { return 0; }\n", text=True, capture_output=True)
        rv32i_compiler = probe.returncode == 0
        if not rv32i_compiler:
            problems.append("RISC-V compiler does not accept the RV32I/ILP32 target")

    commit = None
    if root and (root / ".git").exists():
        result = run(["git", "rev-parse", "HEAD"], cwd=root)
        commit = result.stdout.strip() if result.returncode == 0 else None
        if commit != LITEX_COMMIT:
            problems.append(f"LiteX commit mismatch: expected {LITEX_COMMIT}, got {commit}")
    else:
        problems.append("LiteX source checkout not found; set LITEX_ROOT")

    wishbone = None
    wishbone_test = root / "test/interconnect/test_wishbone.py" if root else None
    if args.wishbone and wishbone_test and wishbone_test.is_file():
        result = run([sys.executable, "-m", "pytest", str(wishbone_test), "-q"], cwd=root)
        wishbone = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        if result.returncode:
            problems.append("LiteX Wishbone baseline failed; see report")
    elif args.wishbone:
        problems.append("LiteX Wishbone test file was not found")

    exit_code = 1 if args.strict and problems else 0
    report = {
        "status": "FAIL" if problems else "PASS", "exit_code": exit_code, "strict": args.strict,
        "python": sys.version.split()[0], "python_supported": python_supported,
        "python_executable": sys.executable, "packages": packages, "soc_packages": soc_packages,
        "tools": tools, "riscv32i_compiler": rv32i_compiler, "verilator_version": verilator_version,
        "litex_root": str(root) if root else None, "litex_commit": commit,
        "expected_litex_commit": LITEX_COMMIT, "vexriscv_rtl": str(rtl_file) if rtl_file else None,
        "expected_pythondata_vex_commit": PYTHONDATA_VEX_COMMIT, "pythondata_vex_commit": vex_commit,
        "wishbone": wishbone, "problems": problems,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for problem in problems:
        print("FAIL 00", problem)
    if not problems:
        print("PASS 00 Environment and Wishbone baseline" if args.wishbone else "PASS 00 Environment")
    print(f"Report: {args.output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
