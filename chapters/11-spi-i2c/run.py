#!/usr/bin/env python3
"""Run pin-level SPI and I2C protocol transactions from VexiiRiscv firmware."""
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
           "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536),
                 "clint": (0xf0010000, 65536), "plic": (0xf0c00000, 4194304)}
REGISTERS = {"i2c_out": (0xf0000000, "rw"), "i2c_input": (0xf0000004, "ro"),
             "spi_out": (0xf0001000, "rw"), "spi_input": (0xf0001004, "ro")}


def check_protocol_log(log):
    lines = log.splitlines()
    expected = ["SPI_FRAME command=0x9f bits=16",
                "I2C_ADDRESS byte=0x86 ack=0",
                "I2C_WRITE index=0 data=0x5a",
                "I2C_WRITE index=1 data=0xc3",
                "I2C_READ index=0 data=0x5a",
                "I2C_READ index=1 data=0xc3",
                "SOC_COMPLETE data=0x0000005a"]
    for marker in expected:
        if marker not in log:
            raise AssertionError(f"缺少协议事件: {marker}")
    if sum(line.startswith("SPI_FRAME") for line in lines) != 1:
        raise AssertionError("错误 CS 请求不应产生 SPI 帧")
    if lines.count("I2C_MASTER_NACK value=1") != 2:
        raise AssertionError("两次 I2C 读末尾均应由主机 NACK")
    for probe in ("0x00001100", "0x000011a5", "0x00001200", "0x0012c35a"):
        if f"PROTOCOL_PROBE value={probe}" not in log:
            raise AssertionError(f"CPU 未完成协议检查 {probe}")


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    import litex
    from litex.build.generic_platform import Pins
    from litex.build.sim import SimPlatform
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder
    from soc import ProjectSoC

    result = ROOT / "results/11"
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
    (result / "csr-header.txt").write_text(header.read_text())

    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("缺少第 00 章 RISC-V gcc/objcopy")
    litex_root = Path(litex.__file__).resolve().parents[1]
    elf = image / "program.elf"
    command = [gcc, "-march=rv32im", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        "-I", str(header.parents[1]),
        "-I", str(litex_root / "litex/soc/cores/cpu/vexiiriscv"),
        "-I", str(litex_root / "litex/soc/software/include"),
        f"-Wl,-T,{CHAPTER / 'linker.ld'}", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"协议固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    build_and_run(root=ROOT, chapter="11", soc=lambda p: ProjectSoC(p, rom_words=words),
        expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS, registers=REGISTERS,
        log_check=check_protocol_log)
    print("PASS 11-SPI-I2C: SPI 帧与 I2C 地址/ACK/寄存器读写均由模型响应")


if __name__ == "__main__":
    main()
