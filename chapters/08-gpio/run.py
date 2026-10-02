#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run, check_generated_map


def check_output_transitions(log):
    values = [line.removeprefix("GPIO_OUTPUT value=0x") for line in log.splitlines()
              if line.startswith("GPIO_OUTPUT value=0x")]
    if not values or values[-1] != "a" or values.count("a") != 1 or any(
            value != "0" for value in values[:-1]):
        raise RuntimeError(f"GPIO 输出应先为 0，再恰好变化一次到 a；观察值: {values}")


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    import litex
    litex_root = Path(litex.__file__).resolve().parents[1]
    from soc import ProjectSoC
    out = ROOT / "results/08/firmware"
    out.mkdir(parents=True, exist_ok=True)
    gcc = shutil.which("riscv64-unknown-elf-gcc")
    if not gcc:
        raise RuntimeError("缺少第 00 章 RISC-V gcc")
    # CSR symbols are generated from this chapter's SoC, so generate them before C compilation.
    # First elaborate the exact design to produce the CSR header and address map.
    from litex.build.generic_platform import Pins
    from litex.build.sim import SimPlatform
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder
    platform = SimPlatform("LITEX_TUTORIAL", [("sys_clk", 0, Pins(1)),
        ("gpio_in", 0, Pins(4)), ("gpio_out", 0, Pins(4))])
    soc = ProjectSoC(platform, rom_words=[0x0000006f])
    soc.crg = CRG(platform.request("sys_clk"))
    soc.finalize()
    builder = Builder(soc, output_dir=str(ROOT / "results/08/builder"),
                      compile_software=False, build_log=True)
    with (ROOT / "results/08/elaborate.log").open("w") as log:
        from contextlib import redirect_stdout, redirect_stderr
        with redirect_stdout(log), redirect_stderr(log):
            builder._generate_includes(with_bios=False)
            builder._generate_csr_map()
        log.write("Generated CSR header and address map from the finalized GPIO SoC.\n")
    header = ROOT / "results/08/builder/software/include/generated/csr.h"
    if not header.is_file():
        raise RuntimeError("Builder 未生成 generated/csr.h")
    regions = {"rom": (0, 4096), "sram": (0x10000000, 4096),
               "main_ram": (0x40000000, 16384),
               "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536),
                 "clint": (0xf0010000, 65536), "plic": (0xf0c00000, 4194304)}
    registers = {"gpio_in_input": (0xf0000000, "ro"),
                 "gpio_out_output": (0xf0000800, "rw")}
    check_generated_map(ROOT / "results/08/builder/csr.csv",
                        regions=regions, registers=registers)
    (ROOT / "results/08/csr-header.txt").write_text(header.read_text())

    # Include the Builder header tree while linking generated CSR accessors.
    image = out
    elf = image / "program.elf"
    command = [gcc, "-march=rv32im", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        "-I", str(header.parents[1]),
        "-I", str(litex_root / "litex/soc/cores/cpu/vexiiriscv"),
        "-I", str(litex_root / "litex/soc/software/include"),
        f"-Wl,-T,{CHAPTER / 'linker.ld'}",
        "-Wl,--defsym=MAIN_RAM_LENGTH=16384", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"),
        str(CHAPTER / "main.c"), "-o", str(elf)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f"GPIO 固件编译失败：{result.stderr}")
    import subprocess as sp
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    sp.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")], check=True)
    readelf = shutil.which("riscv64-unknown-elf-readelf")
    objdump = shutil.which("riscv64-unknown-elf-objdump")
    (image / "sections.txt").write_text(sp.run([readelf, "-S", str(elf)],
        check=True, capture_output=True, text=True).stdout)
    (image / "disassembly.txt").write_text(sp.run([objdump, "-d", "-h", str(elf)],
        check=True, capture_output=True, text=True).stdout)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * ((-len(data)) % 4)
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    if len(data) > 4096:
        raise RuntimeError(f"GPIO 固件 ROM 镜像超限：{len(data)} bytes")

    # Build and run the CPU with the same GPIO-equipped SoC and linked firmware.
    build_and_run(root=ROOT, chapter="08",
        expected="SOC_COMPLETE word_address=0x200003ff data=0x0000005a sel=f",
        soc=lambda p: ProjectSoC(p, rom_words=words),
        regions=regions, registers=registers,
        required_order=("GPIO_OUTPUT value=0xa", "SOC_PROBE data=0x00000000",
                        "GPIO_INPUT_DRIVE value=0x5", "SOC_PROBE data=0x00000005",
                        "SOC_COMPLETE"),
        log_check=check_output_transitions)
    print("PASS 08-GPIO: 输出 GPIO=0xa，CPU 读到输入 GPIO=0x5")


if __name__ == "__main__":
    main()
