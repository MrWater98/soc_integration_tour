#!/usr/bin/env python3
"""Build and execute polling, one-shot IRQ, and periodic IRQ cases."""
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run, check_generated_map

REGIONS = {"rom": (0, 4096), "sram": (0x10000000, 4096),
           "main_ram": (0x40000000, 16384),
           "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536)}
REGISTERS = {
    "timer0_load": (0xf0000800, "rw"), "timer0_reload": (0xf0000804, "rw"),
    "timer0_en": (0xf0000808, "rw"), "timer0_update_value": (0xf000080c, "rw"),
    "timer0_value": (0xf0000810, "ro"), "timer0_ev_status": (0xf0000814, "ro"),
    "timer0_ev_pending": (0xf0000818, "rw"), "timer0_ev_enable": (0xf000081c, "rw"),
}


def check_timer_log(log):
    lines = log.splitlines()
    polls = [line for line in lines if line.startswith("TIMER_POLL ")]
    isrs = [line for line in lines if line.startswith("TIMER_ISR ")]
    asserts = [line for line in lines if line == "IRQ_LINE_ASSERT source=timer0"]
    clears = [line for line in lines if line == "IRQ_LINE_CLEAR source=timer0"]
    if len(polls) != 1 or isrs != [f"TIMER_ISR packed=0x{x:08x}" for x in
                                   (0x00010001, 0x00020002, 0x00020003, 0x00020004)]:
        raise AssertionError(f"轮询/ISR 次数不符: poll={polls}, isr={isrs}")
    if len(asserts) != 4 or len(clears) != 4:
        raise AssertionError(f"IRQ 线边沿数不符: assert={len(asserts)}, clear={len(clears)}")
    if len(polls) == 1:
        packed = int(polls[0].split("=0x", 1)[1], 16)
        first, second = packed & 0xffff, packed >> 16
        if not 0 < second < first <= 600:
            raise AssertionError(f"计数器未按预期递减: {first} -> {second}")
    if lines.index(polls[0]) >= lines.index(isrs[0]):
        raise AssertionError("轮询实验应先于中断实验")


def main():
    add_litex_to_path(ROOT)
    import litex
    from litex.build.generic_platform import Pins
    from litex.build.sim import SimPlatform
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder
    from soc import ProjectSoC

    result = ROOT / "results/10"
    image = result / "firmware"
    image.mkdir(parents=True, exist_ok=True)
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
    header = result / "builder/software/include/generated/csr.h"
    check_generated_map(result / "builder/csr.csv", regions=REGIONS, registers=REGISTERS)
    generated_csv = (result / "builder/csr.csv").read_text()
    irq_row = next((line.split(",") for line in generated_csv.splitlines()
                    if line.startswith("constant,timer0_interrupt,")), None)
    if irq_row is None:
        raise AssertionError("LiteX did not allocate a timer0 IRQ input")
    irq_number = int(irq_row[2])
    if irq_number != 0:
        raise AssertionError(f"Expected the single timer source on VexRiscv input 0, got {irq_number}")
    (result / "irq_map.csv").write_text(f"irq_number,source\n{irq_number},timer0\n")
    (result / "csr-header.txt").write_text(header.read_text())

    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("缺少第 00 章的 RISC-V gcc/objcopy")
    litex_root = Path(litex.__file__).resolve().parents[1]
    elf = image / "program.elf"
    command = [gcc, "-march=rv32i2p0", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        "-I", str(header.parents[1]),
        "-I", str(litex_root / "litex/soc/cores/cpu/vexriscv"),
        "-I", str(litex_root / "litex/soc/software/include"),
        f"-Wl,-T,{CHAPTER / 'linker.ld'}", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"Timer 固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    build_and_run(root=ROOT, chapter="10", soc=lambda p: ProjectSoC(p, rom_words=words),
        expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS, registers=REGISTERS,
        log_check=check_timer_log)
    for mode in ("count", "isr"):
        def check_reset_log(log, mode=mode):
            begin = f"TIMER_RESET_ASSERT mode={mode}"
            end = f"TIMER_RESET_RELEASE mode={mode}"
            if log.count(begin) != 1 or log.count(end) != 1 or log.index(begin) >= log.index(end):
                raise AssertionError(f"{mode} 复位脉冲缺失或重复")
            if mode == "isr":
                probe = log.find("TIMER_ISR packed=0x00010001")
                if probe < 0 or probe > log.index(begin):
                    raise AssertionError("复位未发生在首次 ISR 完成探针时")
            check_timer_log(log.split(end, 1)[1])
        build_and_run(root=ROOT, chapter=f"10-reset-{mode}",
            soc=lambda p, mode=mode: ProjectSoC(p, rom_words=words, reset_mode=mode),
            expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS,
            registers=REGISTERS, log_check=check_reset_log)
    print("PASS 10-TIMER: 轮询递减；1 次 one-shot + 3 次周期中断，均已清除")


if __name__ == "__main__":
    main()
