#!/usr/bin/env python3
"""Build one integrated SoC and execute normal, fault, and seeded reset cases."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import random
import re
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
try:
    from tutorial_paths import add_litex_to_path
except ModuleNotFoundError as exc:
    if exc.name != "tutorial_paths": raise
    # A standalone chapter can use installed LiteX or an explicit source checkout.
    def add_litex_to_path(root):
        if os.environ.get("LITEX_ROOT"):
            source = Path(os.environ["LITEX_ROOT"]).expanduser().resolve()
            if not (source / "litex/__init__.py").is_file():
                raise FileNotFoundError("LITEX_ROOT must contain litex/__init__.py")
            sys.path.insert(0, str(source))
from config import Config
from litex_builder import elaborate, compile_simulator, run_simulator, sha256

STAGES = ("ROM", "RAM", "GPIO", "UART", "TIMER", "SPI", "I2C", "CONCURRENT")


def compile_firmware(result, cfg):
    import litex
    out = result / "firmware"
    out.mkdir(parents=True, exist_ok=True)
    cfg.write_firmware_inputs(out)
    gcc, objcopy, objdump = [shutil.which(f"riscv64-unknown-elf-{tool}") for tool in ("gcc", "objcopy", "objdump")]
    if not all((gcc, objcopy, objdump)):
        raise RuntimeError("Chapter 00 RISC-V gcc/objcopy/objdump are required")
    include = result / "builder/software/include"
    litex_root = Path(litex.__file__).resolve().parents[1]
    elf = out / "program.elf"
    command = [gcc, "-march=rv32im", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
               "-fno-builtin", "-fno-delete-null-pointer-checks", "-nostdlib", "-nostartfiles", "-O1",
               "-I", str(include), "-I", str(out),
               "-I", str(litex_root / "litex/soc/software/include"),
               "-I", str(litex_root / "litex/soc/cores/cpu/vexriscv"),
               f"-Wl,-T,{out/'linker.ld'}", "-Wl,--build-id=none", f"-Wl,-Map={out/'program.map'}",
               str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (out / "link.log").write_text(built.stdout + built.stderr)
    (out / "compile-command.json").write_text(json.dumps(command, indent=2) + "\n")
    if built.returncode: raise RuntimeError(f"firmware compile failed: {built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(out / "program.bin")], check=True, timeout=30)
    disassembly = subprocess.run([objdump, "-d", "-h", str(elf)], capture_output=True, text=True, check=True)
    (out / "disassembly.txt").write_text(disassembly.stdout)
    data = (out / "program.bin").read_bytes()
    # Keep an unused payload word before the checksum trailer for safe corruption.
    if len(data) > cfg.rom_size - 20:
        raise RuntimeError(f"ROM needs {len(data)+20} bytes, configured {cfg.rom_size}")
    data += bytes(cfg.rom_size - 16 - len(data))
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    words += [0x13c0ffee, cfg.tag, sum(words) & 0xffffffff, len(words)]
    (out / "rom_init.hex").write_text("".join(f"{word:08x}\n" for word in words))
    return words


def workload_sequence(seed, count):
    values = []
    x = seed & 0xffffffff
    for _ in range(count):
        x ^= (x << 13) & 0xffffffff
        x ^= x >> 17
        x ^= (x << 5) & 0xffffffff
        x &= 0xffffffff
        values.append(x)
    return values


def serial_bytes(log):
    return bytes(int(value, 16) for value in re.findall(r"UART_TX_BYTE value=0x([0-9a-fA-F]+)", log))


def verify_case(log, cfg, *, name, expected_fail=None, reset_mode=0, reset_count=1, workload_seed=0):
    if reset_mode:
        if log.count("RESET_ASSERT") != reset_count or log.count("RESET_RELEASE") != reset_count:
            raise AssertionError(f"{name}: expected {reset_count} reset pulses")
        assertion = next(line for line in log.splitlines() if line.startswith("RESET_ASSERT"))
        if reset_mode == 2 and "bus_wait=1" not in assertion:
            raise AssertionError("reset must occur during an unanswered Wishbone request")
        if reset_mode == 3 and "irq=1" not in assertion:
            raise AssertionError("reset must occur while the timer IRQ is asserted")
        # Only a complete fresh boot after release can satisfy the recovery check.
        log = log.rsplit("RESET_RELEASE", 1)[1]
    serial = serial_bytes(log).decode("ascii")
    if "UART_FRAME_ERROR" in log or "SIM_TIMEOUT" in log:
        raise AssertionError(f"{name}: unexpected frame error or timeout")
    if expected_fail is not None:
        if f"SOC_FAIL data=0x{expected_fail:08x}" not in log or f"13 FAIL {expected_fail:02X}\n" not in serial:
            raise AssertionError(f"{name}: expected failure 0x{expected_fail:x}, got {serial!r}")
        if "SOC_COMPLETE" in log or "13 ALL PASS" in serial:
            raise AssertionError(f"{name}: failure was incorrectly reported as success")
        completed = {0xe1: 0, 0xe3: 2, 0xe5: 4}[expected_fail]
        observed = [int(value) for value in re.findall(r"SELFTEST_STAGE id=\s*(\d+)", log)]
        if observed != list(range(completed + 1)):
            raise AssertionError(f"{name}: failure occurred at the wrong stage: {observed}")
        for i in range(1, completed + 1):
            if f"13-0{i} {STAGES[i-1]} PASS\n" not in serial:
                raise AssertionError(f"{name}: earlier self-test {i} did not complete")
        if expected_fail == 0xe5:
            if "IRQ_LINE_ASSERT source=timer0" not in log or "IRQ_DIAG pending=1" not in log or "TIMER_ISR" in log:
                raise AssertionError("wrong IRQ must expose pending source and missing ISR")
        return serial
    expected = [f"13-0{i} {stage} PASS\n" for i, stage in enumerate(STAGES, 1)]
    offset = 0
    for text in ["13 BOOT\n", *expected, "13 ALL PASS\n"]:
        position = serial.find(text, offset)
        if position < 0: raise AssertionError(f"{name}: missing/inverted serial result {text!r}")
        offset = position + len(text)
    if serial.count("13 BOOT\n") != 1 or serial.count("13 ALL PASS\n") != 1:
        raise AssertionError(f"{name}: repeated/incomplete boot")
    if log.count("SOC_COMPLETE data=0x0000005a") != 1 or "SOC_FAIL" in log:
        raise AssertionError(f"{name}: incorrect completion status")
    sequence = workload_sequence(workload_seed, cfg.stress_bytes) if workload_seed else []
    payload = "STRESS:" + ("".join(chr(33 + (value >> 8) % 94) for value in sequence)
                           if workload_seed else "".join(chr(65 + i % 26) for i in range(cfg.stress_bytes))) + "\n"
    if workload_seed:
        observed = [int(value, 16) for value in re.findall(r"STRESS_OP encoded=0x([0-9a-f]+)", log)]
        if observed != sequence: raise AssertionError("seeded operation sequence mismatch")
    if payload not in serial: raise AssertionError("long UART loopback differs from configured payload")
    stages = [int(value) for value in re.findall(r"SELFTEST_STAGE id=\s*(\d+)", log)]
    if stages != list(range(9)): raise AssertionError(f"stage evidence mismatch: {stages}")
    irqs = [int(value) for value in re.findall(r"TIMER_ISR count=\s*(\d+)", log)]
    if len(irqs) < 1 + cfg.minimum_irqs or irqs != list(range(1, len(irqs)+1)):
        raise AssertionError(f"IRQ count/progression mismatch: {irqs}")
    # Protocol observations must independently cover the first test plus stress rounds.
    spi_transactions = 1 + (sum((value & 3) == 1 for value in sequence) if workload_seed else (cfg.stress_bytes + 31) // 32)
    transactions = 1 + (sum((value & 3) == 2 for value in sequence) if workload_seed else (cfg.stress_bytes + 31) // 32)
    if len(re.findall(r"SPI_FRAME command=0x[0-9a-f]+ bits=\s*16", log)) != spi_transactions:
        raise AssertionError("SPI transaction count differs; unselected transfers must be ignored")
    if log.count("I2C_MASTER_NACK value=1") != 2 * transactions:
        raise AssertionError("each I2C register read must end with master NACK")
    absent = (cfg.i2c_address ^ 1) << 1
    if f"I2C_ADDRESS byte=0x{absent:02x} ack=0" not in log:
        raise AssertionError("absent I2C address was not observed as NACK")
    for item in ("I2C_WRITE index=0 data=0x5a", "I2C_WRITE index=1 data=0xc3",
                 "I2C_READ index=0 data=0x5a", "I2C_READ index=1 data=0xc3"):
        if log.count(item) != transactions: raise AssertionError(f"protocol evidence count mismatch: {item}")
    # ISR must run inside, not merely before/after, the stress phase.
    positions = {int(stage): match.end() for match in re.finditer(r"SELFTEST_STAGE id=\s*(\d+)", log)
                 for stage in [match.group(1)]}
    if "TIMER_ISR" not in log[positions[7]:positions[8]]:
        raise AssertionError("no interrupt observed while peripherals and memory were active")
    for region in ("sram", "main_ram"):
        base, size = cfg.regions[region]
        for word in (base // 4, (base + size - 4) // 4):
            if f"MEMORY_BOUNDARY name={region} word=0x{word:08x}" not in log:
                raise AssertionError(f"{region}: boundary did not reach the memory bus")
    return serial


def main():
    parser = argparse.ArgumentParser(description="第 13 章整机自检与失效回归")
    parser.add_argument("--case", choices=("all", "normal"), default="all")
    parser.add_argument("--output", type=Path, default=ROOT / "results/13")
    parser.add_argument("--seed", type=int, action="append", help="UART reset seeds; default 13,97")
    for name in ("gpio_width", "rom_size", "sram_size", "main_ram_size", "stack_size",
                 "sys_clk_hz", "baud", "timer_period", "response_wait", "stress_bytes", "max_cycles"):
        parser.add_argument("--" + name.replace("_", "-"), type=lambda text: int(text, 0))
    args = parser.parse_args()
    cfg = Config(**{key: getattr(args, key) for key in Config.__dataclass_fields__
                    if hasattr(args, key) and getattr(args, key) is not None}).validate()
    result = args.output.resolve()
    result.mkdir(parents=True, exist_ok=True)
    (result / "summary.json").unlink(missing_ok=True)
    (result / "config.json").write_text(json.dumps(cfg.values, indent=2) + "\n")
    add_litex_to_path(ROOT)
    from soc import TutorialSoC
    elaborate(result, cfg, TutorialSoC, rom_words=[0x0000006f])
    words = compile_firmware(result, cfg)
    elaborate(result, cfg, TutorialSoC, rom_words=words, emit_rtl=True)
    print(f"BUILD 13: config={cfg.digest[:12]}, ROM={cfg.rom_size}, GPIO={cfg.gpio_width}", flush=True)
    compile_simulator(result)
    import litex
    from litex import get_data_mod
    versions = {"python": sys.version, "migen": importlib.metadata.version("migen"),
                "vexriscv_data_git_hash": get_data_mod("cpu", "vexriscv").data_git_hash}
    for tool in ("verilator", "riscv64-unknown-elf-gcc", "g++"):
        versions[tool] = subprocess.run([tool, "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0]
    versions["litex_git"] = subprocess.run(["git", "-C", str(Path(litex.__file__).resolve().parents[1]),
                                            "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    manifest = {"config": cfg.values, "config_sha256": cfg.digest,
                "tools": versions,
                "firmware_sha256": sha256(result / "firmware/program.bin"),
                "rom_hex_sha256": sha256(result / "firmware/rom_init.hex"),
                "csr_map_sha256": sha256(result / "builder/csr.csv"),
                "rtl_sources": json.loads((result / "rtl/sources.json").read_text()),
                "source_sha256": {p.name: sha256(p) for p in CHAPTER.iterdir()
                                  if p.is_file() and p.suffix in (".py", ".S", ".c", ".v")}}
    (result / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cases = [("normal", [], None, 0, False)]
    if args.case == "all":
        cases += [("wrong-csr", ["+fault=1"], 0xe3, 0, False),
                  ("wrong-irq", ["+fault=2"], 0xe5, 0, False),
                  ("corrupt-rom", [], 0xe1, 0, True)]
        for seed in args.seed or (13, 97):
            delay = random.Random(seed).randrange(1, 4 * cfg.bit_cycles - 1)
            cases.append((f"reset-uart-{seed}", ["+reset_mode=1", f"+seed={seed}", f"+reset_delay={delay}"], None, 1, False))
        cases += [("reset-bus", ["+reset_mode=2", "+seed=13", "+reset_delay=0"], None, 2, False),
                  ("reset-irq", ["+reset_mode=3", "+seed=13", "+reset_delay=0"], None, 3, False)]
    summary = []
    for name, arguments, error, reset_mode, corrupt in cases:
        log = run_simulator(result, name, arguments, manifest=manifest, corrupt_rom=corrupt)
        serial = verify_case(log, cfg, name=name, expected_fail=error, reset_mode=reset_mode)
        (result / "cases" / f"{name}.uart.txt").write_text(serial)
        summary.append({"case": name, "status": "PASS", "expected_failure": error, "reset_mode": reset_mode})
        print(f"PASS 13-{name}: " + (f"captured 0x{error:x}" if error else "eight self-tests and serial/protocol/IRQ evidence"), flush=True)
    (result / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"PASS 13-INTEGRATION: {len(cases)} cases; results: {result}")


if __name__ == "__main__":
    main()
