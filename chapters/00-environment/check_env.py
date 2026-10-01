#!/usr/bin/env python3
"""Stage 00: verify the pinned host tools and source baseline."""

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
PYTHONDATA_VEX_COMMIT = "15cfab529a17c473d0fc75edf3f409eb374cef35"
VEXII_GENERATOR_COMMIT = "235753e24f2d960e49a0852205bae1400bf22c19"
SBT_PROJECT_VERSION = "1.10.0"
EXPECTED_PACKAGES = {
    "migen": "0.9.2",
    "pytest": "9.0.3",
    "pythondata-cpu-vexiiriscv": "1.0.1.post325",
    "pythondata-software-picolibc": "1.7.9.post181",
    "pythondata-software-compiler-rt": "0.0.post6206",
    "pythondata-misc-tapcfg": "0.0.post517",
}
CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path


def command(args, cwd=None, timeout=120):
    return subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)


def main():
    parser = argparse.ArgumentParser(description="Verify the SoC integration host environment")
    parser.add_argument("--strict", action="store_true", help="return failure for any missing requirement")
    parser.add_argument("--wishbone", action="store_true", help="run LiteX's Wishbone baseline test")
    parser.add_argument("--soc", action="store_true", help="check SoCCore/Builder simulation dependencies")
    parser.add_argument("--require-tool", action="append", default=[], help="require an additional executable")
    parser.add_argument("--output", type=Path, default=Path("results/00/environment.json"))
    args = parser.parse_args()

    problems = []
    python_version = sys.version_info[:2]
    python_supported = (3, 10) <= python_version < (3, 12)
    if not python_supported:
        problems.append(f"Python 3.10 or 3.11 is required; found {sys.version.split()[0]}")

    packages = {}
    for name in ("migen", "pytest", "pythondata-cpu-vexiiriscv"):
        try:
            packages[name] = importlib.metadata.version(name)
            if packages[name] != EXPECTED_PACKAGES[name]:
                problems.append(
                    f"Python package version mismatch for {name}: "
                    f"expected {EXPECTED_PACKAGES[name]}, got {packages[name]}"
                )
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
            problems.append(f"Missing Python package: {name}")
    soc_packages = {}
    if args.soc:
        for name in ("pythondata-software-picolibc", "pythondata-software-compiler-rt",
                     "pythondata-misc-tapcfg"):
            try:
                soc_packages[name] = importlib.metadata.version(name)
                if soc_packages[name] != EXPECTED_PACKAGES[name]:
                    problems.append(
                        f"Python package version mismatch for {name}: "
                        f"expected {EXPECTED_PACKAGES[name]}, got {soc_packages[name]}"
                    )
            except importlib.metadata.PackageNotFoundError:
                soc_packages[name] = None
                problems.append(f"Missing SoCCore/Builder Python package: {name}")
        c_compiler = shutil.which("cc") or shutil.which("gcc")
        json_header = False
        if c_compiler:
            probe = subprocess.run([c_compiler, "-E", "-x", "c", "-"],
                input="#include <json-c/json.h>\n", text=True, capture_output=True)
            json_header = probe.returncode == 0
        if not json_header:
            problems.append("Missing json-c development header (install libjson-c-dev on Debian/Ubuntu)")

    vex_source = None
    try:
        direct_url = importlib.metadata.distribution("pythondata-cpu-vexiiriscv").read_text("direct_url.json")
        if direct_url:
            origin = json.loads(direct_url)
            vex_source = origin.get("vcs_info", {}).get("commit_id")
            if vex_source is None and origin.get("url", "").startswith("file://"):
                source_dir = Path(origin["url"][7:])
                if (source_dir / ".git").exists():
                    result = command(["git", "rev-parse", "HEAD"], cwd=source_dir)
                    vex_source = result.stdout.strip() if result.returncode == 0 else None
        if vex_source != PYTHONDATA_VEX_COMMIT:
            problems.append(f"VexiiRiscv RTL source commit mismatch or unknown: {vex_source}")
    except importlib.metadata.PackageNotFoundError:
        pass

    tools = {}
    required_tools = ("verilator", "git", "riscv64-unknown-elf-gcc", "riscv64-unknown-elf-objcopy", "sbt", "java", *args.require_tool)
    for name in required_tools:
        tools[name] = shutil.which(name)
        if tools[name] is None:
            problems.append(f"Missing executable: {name}")
    compiler = os.environ.get("CXX") or shutil.which("g++-11") or shutil.which("g++")
    cpp20 = False
    if compiler:
        probe = subprocess.run(
            [compiler, "-std=c++20", "-x", "c++", "-fsyntax-only", "-"],
            input="#include <coroutine>\nint main() { return 0; }\n",
            text=True, capture_output=True,
        )
        cpp20 = probe.returncode == 0
    if not cpp20:
        problems.append("Missing C++20 compiler with <coroutine> support")
    riscv32im = False
    if tools["riscv64-unknown-elf-gcc"]:
        probe = subprocess.run(
            [tools["riscv64-unknown-elf-gcc"], "-march=rv32im", "-mabi=ilp32",
             "-x", "c", "-fsyntax-only", "-"],
            input="int main(void) { return 0; }\n",
            text=True, capture_output=True,
        )
        riscv32im = probe.returncode == 0
    if not riscv32im:
        problems.append("RISC-V compiler does not accept the required RV32IM/ILP32 target")

    verilator_version = command(["verilator", "--version"]).stdout.strip() if tools["verilator"] else None
    verilator_match = re.search(r"Verilator\s+(\d+)", verilator_version or "")
    if tools["verilator"] and (not verilator_match or int(verilator_match.group(1)) < 5):
        problems.append(f"Verilator 5 or newer is required; found {verilator_version}")
    java_version = None
    if tools["java"]:
        java_result = command(["java", "-version"])
        java_text = java_result.stderr + java_result.stdout
        java_match = re.search(r"(?:openjdk|java)(?: version)?\s+[\"']?(\d+)", java_text, re.IGNORECASE)
        java_version = java_match.group(1) if java_match else java_text.strip().splitlines()[0]
        if java_match and int(java_match.group(1)) < 11:
            problems.append(f"Java 11 or newer is required; found {java_version}")

    root = add_litex_to_path(ROOT)
    try:
        import litex
        from litex import get_data_mod

        if root is None:
            root = Path(litex.__file__).resolve().parents[1]
        from litex.soc.cores.cpu import CPUS
        from litex.soc.cores.cpu.vexiiriscv.core import VexiiRiscv
        if CPUS.get("vexiiriscv") is not VexiiRiscv:
            problems.append("LiteX CPU registry does not expose the native vexiiriscv core")
        rtl = Path(get_data_mod("cpu", "vexiiriscv").data_location) / "ext/VexiiRiscv/build.sbt"
        if not rtl.is_file():
            problems.append(f"Missing VexiiRiscv Scala RTL generator source: {rtl}")
        generator_root = rtl.parent
        if (generator_root / ".git").exists():
            result = command(["git", "rev-parse", "HEAD"], cwd=generator_root)
            generator_commit = result.stdout.strip() if result.returncode == 0 else None
        else:
            generator_commit = None
        if generator_commit != VEXII_GENERATOR_COMMIT:
            problems.append(
                f"VexiiRiscv generator commit mismatch: "
                f"expected {VEXII_GENERATOR_COMMIT}, got {generator_commit}"
            )
        build_properties = generator_root / "project/build.properties"
        sbt_version = None
        if build_properties.is_file():
            for line in build_properties.read_text().splitlines():
                if line.startswith("sbt.version="):
                    sbt_version = line.split("=", 1)[1].strip()
                    break
        if sbt_version != SBT_PROJECT_VERSION:
            problems.append(
                f"sbt project version mismatch: expected {SBT_PROJECT_VERSION}, got {sbt_version}"
            )
    except Exception as exc:
        rtl = None
        problems.append(f"LiteX/VexiiRiscv import failed: {exc}")

    commit = None
    if root is not None and (root / ".git").exists():
        result = command(["git", "rev-parse", "HEAD"], cwd=root)
        if result.returncode == 0:
            commit = result.stdout.strip()
        if commit != LITEX_COMMIT:
            problems.append(f"LiteX commit mismatch: expected {LITEX_COMMIT}, got {commit}")
    else:
        problems.append("LiteX source checkout with .git was not found; set LITEX_ROOT")

    wishbone = None
    if args.wishbone and root is not None and (root / "test/interconnect/test_wishbone.py").is_file():
        try:
            result = command(
                [sys.executable, "-m", "pytest", "test/interconnect/test_wishbone.py", "-q"],
                cwd=root,
            )
            wishbone = {"exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
            if result.returncode != 0:
                problems.append("LiteX Wishbone baseline failed; inspect the wishbone field in the JSON report")
        except subprocess.TimeoutExpired:
            wishbone = {"error": "120 second timeout"}
            problems.append("LiteX Wishbone baseline timed out")
    elif args.wishbone:
        problems.append("LiteX Wishbone test file was not found")

    exit_code = 1 if args.strict and problems else 0
    report = {
        "status": "FAIL" if problems else "PASS",
        "exit_code": exit_code,
        "strict": args.strict,
        "requested_extra_tools": args.require_tool,
        "wishbone_requested": args.wishbone,
        "python": sys.version.split()[0],
        "python_supported": python_supported,
        "python_executable": sys.executable,
        "packages": packages,
        "soc_packages": soc_packages,
        "soc_dependencies_requested": args.soc,
        "tools": tools,
        "cxx": compiler,
        "cxx20_coroutine": cpp20,
        "riscv32im_compiler": riscv32im,
        "verilator_version": verilator_version,
        "java_version": java_version,
        "litex_root": str(root) if root else None,
        "litex_commit": commit,
        "expected_litex_commit": LITEX_COMMIT,
        "vexii_source": str(rtl) if rtl else None,
        "expected_pythondata_vex_commit": PYTHONDATA_VEX_COMMIT,
        "pythondata_vex_commit": vex_source,
        "expected_vexii_generator_commit": VEXII_GENERATOR_COMMIT,
        "vexii_generator_commit": generator_commit if rtl else None,
        "sbt_project_version": sbt_version if rtl else None,
        "vexii_cpu_type": "vexiiriscv",
        "wishbone": wishbone,
        "problems": problems,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for item in problems:
        print("FAIL 00", item)
    if not problems:
        print("PASS 00 Environment and Wishbone baseline" if args.wishbone else "PASS 00 Environment (Wishbone test not requested)")
    print(f"Report: {args.output}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
