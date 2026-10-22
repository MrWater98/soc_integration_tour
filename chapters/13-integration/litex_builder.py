"""Local Chapter 13 helpers: emit headers/RTL, compile, and run the same SoC."""
from contextlib import redirect_stderr, redirect_stdout
import csv
import ctypes.util
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_map(path):
    with path.open(newline="") as stream:
        return list(csv.reader(line for line in stream if not line.startswith("#")))


def check_generated_map(path, cfg):
    rows = read_map(path)
    actual = {r[1]: (int(r[2], 0), int(r[3])) for r in rows if r and r[0] == "memory_region"}
    if actual != cfg.regions:
        raise AssertionError(f"hardware/firmware region mismatch: {actual} != {cfg.regions}")
    bases = {r[1]: int(r[2], 0) for r in rows if r and r[0] == "csr_base"}
    selected = {"gpio_in": 0, "gpio_out": 1, "uart": 2, "timer0": 3,
                "spi": 4, "i2c": 5, "identifier_mem": 6}
    # This selected SoCCore configuration uses 0x800-byte CSR pages.
    expected = {name: cfg.regions["csr"][0] + slot * 0x800 for name, slot in selected.items()}
    if bases != expected:
        raise AssertionError(f"CSR allocation mismatch: {bases} != {expected}")
    constants = {r[1]: r[2] for r in rows if r and r[0] == "constant"}
    if constants.get("timer0_interrupt") != "0" or constants.get("uart_interrupt") != "1":
        raise AssertionError("selected IRQ map must be timer0=0, uart=1")
    return rows


def elaborate(result, cfg, design_factory, *, rom_words, emit_rtl=False, coverage=False, trace=True):
    from litex.build.generic_platform import Pins
    from litex.build.io import CRG
    from litex.build.sim import SimPlatform
    from litex.build.sim.config import SimConfig
    from litex.soc.integration.builder import Builder

    output = result / "builder"
    result.mkdir(parents=True, exist_ok=True)
    platform = SimPlatform("LITEX_TUTORIAL", [("sys_clk", 0, Pins(1))])
    with (result / ("build.log" if emit_rtl else "elaborate.log")).open("w") as log:
        with redirect_stdout(log), redirect_stderr(log):
            design = design_factory(platform, cfg=cfg, rom_words=rom_words)
            design.crg = CRG(platform.request("sys_clk"), rst=design.test_reset)
            builder = Builder(design, output_dir=str(output), compile_software=False, build_log=True)
            if emit_rtl:
                builder.build(sim_config=SimConfig(default_clk="sys_clk", default_clk_freq=cfg.sys_clk_hz),
                              run=False, trace_fst=trace, coverage=coverage, opt_level="O2")
            else:
                design.finalize()
                builder._generate_includes(with_bios=False)
                builder._generate_csr_map()
    check_generated_map(output / "csr.csv", cfg)
    if emit_rtl:
        snapshot = result / "rtl"
        snapshot.mkdir(parents=True, exist_ok=True)
        sources = []
        gateware = output / "gateware"
        # Include every registered HDL source, including the external CPU and models.
        paths = [Path(source[0]) for source in platform.sources]
        paths += list(gateware.glob("*.init"))
        names = {}
        for path in paths:
            if not path.is_absolute(): path = gateware / path
            if path.suffix not in (".v", ".sv", ".vh", ".init"): continue
            if path.name in names and names[path.name] != path.resolve():
                raise RuntimeError(f"RTL snapshot filename collision: {path.name}")
            names[path.name] = path.resolve()
            target = snapshot / path.name
            target.write_text("\n".join(line.rstrip() for line in path.read_text().splitlines()).rstrip() + "\n")
            sources.append({"file": path.name, "origin": str(path.resolve()),
                            "source_sha256": sha256(path), "snapshot_sha256": sha256(target)})
        (snapshot / "sources.json").write_text(json.dumps(sources, indent=2) + "\n")
        shutil.copyfile(output / "csr.csv", result / "memory_map.csv")
        (result / "irq_map.csv").write_text("irq_number,source,firmware_mode\n0,timer0,interrupt\n1,uart,polling\n")
    return output


def compile_simulator(result):
    gateware = result / "builder/gateware"
    line = next(line for line in (gateware / "build_sim.sh").read_text().splitlines()
                if line.startswith("make -C"))
    arguments = shlex.split(line)[1:]
    core = Path(arguments[arguments.index("-f") + 1]).parent
    shutil.rmtree(gateware / "modules", ignore_errors=True)
    (gateware / "modules").mkdir()
    with (result / "compile.log").open("w") as log:
        subprocess.run(["make", "-C", "modules", "-f", str(core / "modules/Makefile"), "clocker"],
                       cwd=gateware, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
        jsonc = ctypes.util.find_library("json-c")
        link = f"-l:{jsonc}" if jsonc and jsonc.startswith("lib") else "-ljson-c"
        arguments += ["sim", f"LDFLAGS=-lpthread {link} -lz -lm -lstdc++ -ldl -levent"]
        subprocess.run(["make", *arguments], cwd=gateware, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=300)
    return gateware / "obj_dir/Vsim"


def run_simulator(result, name, arguments, *, manifest, corrupt_rom=False, timeout=60, require_wave=True):
    gateware = result / "builder/gateware"
    cases = result / "cases"
    cases.mkdir(exist_ok=True)
    rom = gateware / "sim_rom.init"
    saved = rom.read_bytes()
    for stale in ("sim.fst", "sim.cov"):
        (gateware / stale).unlink(missing_ok=True)
    try:
        if corrupt_rom:
            words = rom.read_text().splitlines()
            # Last payload word is padding, outside executing code and before the trailer.
            words[-5] = f"{int(words[-5], 16) ^ 1:08x}"
            rom.write_text("\n".join(words) + "\n")
        case_manifest = {**manifest, "case": name, "arguments": arguments,
                         "loaded_rom_init_sha256": sha256(rom), "corrupt_rom": corrupt_rom}
        run = subprocess.run([str((gateware / "obj_dir/Vsim").resolve()), *arguments],
                             cwd=gateware, capture_output=True, text=True, timeout=timeout)
        log = run.stdout + run.stderr
        (cases / f"{name}.log").write_text(log)
        case_manifest["exit_code"] = run.returncode
        wave = gateware / "sim.fst"
        if require_wave and (not wave.exists() or wave.stat().st_size < 256):
            raise RuntimeError(f"{name}: missing waveform")
        if wave.exists(): shutil.move(str(wave), cases / f"{name}.fst")
        coverage = gateware / "sim.cov"
        if coverage.exists(): shutil.move(str(coverage), cases / f"{name}.cov")
        (cases / f"{name}.json").write_text(json.dumps(case_manifest, indent=2) + "\n")
        if run.returncode:
            raise RuntimeError(f"{name}: simulator exited {run.returncode}; see {cases/name}.log\n{log[-2000:]}")
        return log
    except subprocess.TimeoutExpired as exc:
        def decode(data): return data.decode(errors="replace") if isinstance(data, bytes) else (data or "")
        (cases / f"{name}.log").write_text(decode(exc.stdout) + decode(exc.stderr))
        case_manifest["timeout_seconds"] = timeout
        (cases / f"{name}.json").write_text(json.dumps(case_manifest, indent=2) + "\n")
        raise
    finally:
        rom.write_bytes(saved)
