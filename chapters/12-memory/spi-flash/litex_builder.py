"""Chapter 12 SPI Flash build and simulation helpers."""
from contextlib import redirect_stdout, redirect_stderr
import ctypes.util
import csv
import re
from pathlib import Path
import shlex
import shutil
import subprocess

def export_work_rtl(root, chapter, gateware):
    """Copy the exact Verilog and memory-init inputs used by this simulation."""
    destination = Path(root) / "results" / chapter / "rtl"
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True, exist_ok=True)

    build_script = (gateware / "build_sim.sh").read_text()
    line = next((item for item in build_script.splitlines() if item.startswith("make -C")), None)
    match = re.search(r'CC_SRCS="([^"]*)"', line or "")
    if not match:
        raise RuntimeError(f"No CC_SRCS list found in {gateware / 'build_sim.sh'}")
    tokens = shlex.split(match.group(1))
    manifest = ["Verilog inputs passed to the simulator compiler:"]
    def source_label(path):
        try:
            return str(path.resolve().relative_to(Path(root).resolve()))
        except ValueError:
            parts = path.resolve().parts
            if "pythondata_cpu_vexriscv" in parts:
                return str(Path(*parts[parts.index("pythondata_cpu_vexriscv"):]))
            return path.name
    copied = []
    for index, token in enumerate(tokens[:-1]):
        if token != "--cc":
            continue
        source = Path(tokens[index + 1])
        if not source.is_absolute():
            source = gateware / source
        if not source.is_file():
            raise FileNotFoundError(f"Simulator RTL input is missing: {source}")
        target = destination / source.name
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise RuntimeError(f"Two simulator inputs share a filename: {source.name}")
        shutil.copyfile(source, target)
        copied.append(target)
        manifest.append(f"{target.name} <- {source_label(source)}")

    init_names = set()
    for source in copied:
        if source.suffix.lower() not in (".v", ".sv"):
            continue
        init_names.update(re.findall(r'\$(?:readmemh|readmemb)\s*\(\s*"([^"]+)"',
                                     source.read_text(errors="replace")))
    for name in sorted(init_names):
        source = gateware / name
        if not source.is_file():
            raise FileNotFoundError(f"RTL initialization file is missing: {source}")
        target = destination / Path(name).name
        shutil.copyfile(source, target)
        manifest.append(f"{target.name} <- {source_label(source)} (memory initialization data)")
    (destination / "rtl_sources.txt").write_text("\n".join(manifest) + "\n")



def check_generated_map(csv_path, *, regions):
    """Reject a SoC whose generated software addresses differ from the firmware contract."""
    with csv_path.open(newline="") as source:
        rows = list(csv.reader(line for line in source if not line.startswith("#")))
    actual_regions = {row[1]: (int(row[2], 0), int(row[3]))
                      for row in rows if row and row[0] == "memory_region"}
    if actual_regions != regions:
        raise AssertionError(f"生成的 memory_region 与预期不符: {actual_regions} != {regions}")


def build_and_run(*, root, soc, chapter, expected, regions, post_build_check=None, log_check=None):
    from litex.build.generic_platform import Pins
    from litex.build.sim import SimPlatform
    from litex.build.sim.config import SimConfig
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder

    result_dir = root / "results" / chapter
    output = result_dir / "builder"
    output.mkdir(parents=True, exist_ok=True)
    platform = SimPlatform("LITEX_TUTORIAL", [("sys_clk", 0, Pins(1))])
    design = soc(platform)
    design.crg = CRG(platform.request("sys_clk"))
    sim_config = SimConfig(default_clk="sys_clk", default_clk_freq=1_000_000)
    builder = Builder(design, output_dir=str(output), compile_software=False, build_log=True)
    with (result_dir / "build.log").open("w") as log:
        with redirect_stdout(log), redirect_stderr(log):
            builder.build(sim_config=sim_config, run=False, trace=True, opt_level="O2")
    litex_log = output / "litex.log"
    if litex_log.is_file():
        shutil.copyfile(litex_log, result_dir / "build.log")
    csv_path = output / "csr.csv"
    check_generated_map(csv_path, regions=regions)
    generated_csv = csv_path.read_text()
    (result_dir / "memory_map.csv").write_text(generated_csv)
    if "constant,config_cpu_interrupts,0,," not in generated_csv:
        raise AssertionError("本阶段应关闭 CPU 中断，生成配置却并非 0 个中断")
    (result_dir / "irq_map.csv").write_text("irq_number,source\n")
    if post_build_check is not None:
        post_build_check(output)
    export_work_rtl(root, chapter, output / "gateware")
    gateware = output / "gateware"
    build_script = (gateware / "build_sim.sh").read_text()
    make_line = next(line for line in build_script.splitlines() if line.startswith("make -C"))
    make_args = shlex.split(make_line)[1:]
    # The generated default target also compiles every optional simulator plugin
    # (Ethernet/video/etc.). This CPU-only tutorial needs only the core simulator.
    shutil.rmtree(gateware / "modules", ignore_errors=True)
    (gateware / "modules").mkdir()
    core_dir = Path(make_args[make_args.index("-f") + 1]).parent
    with (result_dir / "compile.log").open("w") as log:
        subprocess.run(["make", "-C", "modules", "-f", str(core_dir / "modules/Makefile"),
                        "clocker"], cwd=gateware, stdout=log, stderr=subprocess.STDOUT,
                       check=True, timeout=120)
    jsonc = ctypes.util.find_library("json-c")
    jsonc_link = f"-l:{jsonc}" if jsonc and jsonc.startswith("lib") else "-ljson-c"
    make_args.extend(["sim", f"LDFLAGS=-lpthread {jsonc_link} -lz -lm -lstdc++ -ldl -levent"])
    with (result_dir / "compile.log").open("a") as log:
        subprocess.run(["make", *make_args], cwd=gateware, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=300)
    result = subprocess.run([str(gateware / "obj_dir/Vsim")], cwd=gateware,
                            capture_output=True, text=True, timeout=30)
    log = result.stdout + result.stderr
    (result_dir / "run.log").write_text(log)
    if result.returncode != 0 or expected not in log:
        raise RuntimeError(f"仿真未观察到 {expected}；查看 results/{chapter}/run.log\n{log}")
    if log_check is not None:
        log_check(log)
    print(log.strip())
    print(f"PASS {chapter}: CPU 运行成功；LiteX 生成文件位于 {output}")
    return output
