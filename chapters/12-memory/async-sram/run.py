#!/usr/bin/env python3
"""Run the LiteX AsyncSRAM bridge against a real byte-wide pin model."""
from pathlib import Path
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent.parent if CHAPTER.parent.name == "12-memory" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run

REGIONS = {"rom": (0, 4096), "sram": (0x10000000, 4096),
           "ext_sram": (0x90000000, 4096), "main_ram": (0x40000000, 16384),
           "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536)}


def check_log(log):
    for marker in ("ASRAM_PROBE value=0x11223344", "ASRAM_PROBE value=0x1122aa44",
                   "ASRAM_PROBE value=0x55667788", "ASRAM_PROBE value=0x00000008",
                   "ASRAM_PAD_WRITE byte=0x000 data=0x44",
                   "ASRAM_PAD_WRITE byte=0xfff data=0x55"):
        if marker not in log:
            raise AssertionError(f"SRAM 模型缺少证据: {marker}")
    waits = [int(line.rsplit("wait=", 1)[1]) for line in log.splitlines()
             if line.startswith("ASRAM_ACK ")]
    if len(waits) < 20 or min(waits) < 1 or max(waits) > 31:
        raise AssertionError(f"异步 SRAM 应答等待时间异常: {waits}")
    if "sel=2" not in log:
        raise AssertionError("未观察到字节通道 1 的部分写")


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    result = ROOT / "results/12-async-sram"
    image = result / "firmware"
    image.mkdir(parents=True, exist_ok=True)
    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("缺少第 00 章 RISC-V 工具链")
    elf = image / "program.elf"
    command = [gcc, "-march=rv32i2p0", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        f"-Wl,-T,{CHAPTER / 'linker.ld'}", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"SRAM 固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    build_and_run(root=ROOT, chapter="12-async-sram",
        soc=lambda p: ProjectSoC(p, rom_words=words), regions=REGIONS,
        expected="SOC_COMPLETE data=0x0000005a", log_check=check_log)
    print("PASS 12-ASYNC-SRAM: 外部 8 位模型完成 32 位读写、部分写和边界访问")


if __name__ == "__main__":
    main()
