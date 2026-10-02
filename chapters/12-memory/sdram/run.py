#!/usr/bin/env python3
"""Initialize a LiteDRAM SDR model, then test writes, boundaries and refresh."""
from contextlib import redirect_stderr, redirect_stdout
import os
from pathlib import Path
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent.parent if CHAPTER.parent.name == "12-memory" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run, check_generated_map

REGIONS = {"rom": (0, 4096), "sram": (0x10000000, 4096),
           "main_ram": (0x40000000, 4*1024*1024),
           "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536),
                 "clint": (0xf0010000, 65536), "plic": (0xf0c00000, 4194304)}


def check_log(log):
    events = ["SDRAM_PROBE value=0x00000001", "SDRAM_PROBE value=0x00000002",
              "SDRAM_PROBE value=0x00000003", "SOC_COMPLETE data=0x0000005a"]
    position = -1
    for event in events:
        position = log.find(event, position + 1)
        if position < 0:
            raise AssertionError(f"SDRAM 初始化/读回阶段缺少或乱序: {event}")
    counts = [line for line in log.splitlines() if line.startswith("SDRAM_REFRESH_COUNT ")]
    if len(counts) != 1:
        raise AssertionError("缺少刷新命令计数")
    before_text, after_text = counts[0].removeprefix("SDRAM_REFRESH_COUNT before=").split(" after=")
    before, after = int(before_text, 16), int(after_text, 16)
    if after < before + 2:
        raise AssertionError(f"数据写入后自动刷新不足两次: {before} -> {after}")


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    litedram_root = os.environ.get("LITEDRAM_ROOT")
    if litedram_root:
        source = Path(litedram_root).expanduser().resolve()
        if not (source / "litedram/__init__.py").is_file():
            raise RuntimeError("LITEDRAM_ROOT 应指向含 litedram/__init__.py 的源码根目录")
        sys.path.insert(0, str(source))
    try:
        import litedram
    except ModuleNotFoundError as exc:
        raise RuntimeError("第 12 章 SDRAM 实验需要 LiteDRAM；请安装或设置 LITEDRAM_ROOT") from exc
    import litex
    from compat import enable_python311_csr_names
    enable_python311_csr_names()
    from litex.build.generic_platform import Pins
    from litex.build.sim import SimPlatform
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder
    from soc import ProjectSoC

    result = ROOT / "results/12-sdram"
    image = result / "firmware"
    image.mkdir(parents=True, exist_ok=True)
    (result / "dependency.txt").write_text(
        f"LiteDRAM source: {Path(litedram.__file__).resolve()}\n"
        f"LiteX source: {Path(litex.__file__).resolve()}\n")
    platform = SimPlatform("LITEX_TUTORIAL", [("sys_clk", 0, Pins(1))])
    soc = ProjectSoC(platform, rom_words=[0x0000006f])
    soc.crg = CRG(platform.request("sys_clk"))
    soc.finalize()
    builder = Builder(soc, output_dir=str(result / "builder"),
                      compile_software=False, build_log=True)
    with (result / "elaborate.log").open("w") as log:
        with redirect_stdout(log), redirect_stderr(log):
            builder._generate_includes(with_bios=False)
            builder._generate_csr_map()
    header_dir = result / "builder/software/include/generated"
    check_generated_map(result / "builder/csr.csv", regions=REGIONS)
    if not (header_dir / "sdram_phy.h").is_file():
        raise AssertionError("LiteDRAM 初始化序列头文件没有生成")
    (result / "sdram-phy-header.txt").write_text((header_dir / "sdram_phy.h").read_text())

    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("缺少第 00 章 RISC-V 工具链")
    litex_root = Path(litex.__file__).resolve().parents[1]
    elf = image / "program.elf"
    command = [gcc, "-march=rv32im", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        "-I", str(header_dir.parent),
        "-I", str(litex_root / "litex/soc/cores/cpu/vexiiriscv"),
        "-I", str(litex_root / "litex/soc/software/include"),
        f"-Wl,-T,{CHAPTER / 'linker.ld'}", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"SDRAM 固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    build_and_run(root=ROOT, chapter="12-sdram",
        soc=lambda p: ProjectSoC(p, rom_words=words), regions=REGIONS,
        expected="SOC_COMPLETE data=0x0000005a", log_check=check_log)
    print("PASS 12-SDRAM: LiteDRAM 初始化、4 MiB 边界/数据模式、刷新后读回")


if __name__ == "__main__":
    main()
