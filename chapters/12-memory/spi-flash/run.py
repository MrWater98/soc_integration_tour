#!/usr/bin/env python3
"""Check a Wishbone read-only window backed by pin-level SPI Flash reads."""
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
           "main_ram": (0x40000000, 16384), "completion": (0x80000000, 4096),
           "flash": (0xa0000000, 4096), "csr": (0xf0000000, 65536)}


def check_log(log):
    for marker in ("FLASH_PROBE value=0x46434f53",
                   "FLASH_READ command=0x03 addr=0x000000 bits=64",
                   "FLASH_READ command=0x03 addr=0x0000fc bits=64",
                   "FLASH_READ command=0x03 addr=0x000ffc bits=64"):
        if marker not in log:
            raise AssertionError(f"SPI Flash 缺少协议证据: {marker}")
    reads = [line for line in log.splitlines() if line.startswith("FLASH_READ ")]
    if len(reads) < 65 or any("command=0x03" not in line or "bits=64" not in line
                            for line in reads):
        raise AssertionError(f"SPI Flash 交易长度/命令异常，交易数 {len(reads)}")


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    result = ROOT / "results/12-spi-flash"
    image = result / "firmware"
    image.mkdir(parents=True, exist_ok=True)

    content = bytearray(b"SOCF" + (256).to_bytes(4, "little"))
    content.extend(((i * 37 + 11) & 0xff) for i in range(8, 252))
    checksum = sum(content) & 0xffffffff
    content.extend(checksum.to_bytes(4, "little"))
    content.extend(b"\xff" * (4096 - len(content)))
    (result / "flash_image.bin").write_bytes(content)
    (result / "flash_image.hex").write_text("".join(f"{byte:02x}\n" for byte in content))
    (result / "image-check.txt").write_text(
        f"capacity_bytes=4096\nimage_bytes=256\nchecksum=0x{checksum:08x}\n")

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
        raise RuntimeError(f"Flash 固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))

    def place_image(output):
        shutil.copyfile(result / "flash_image.hex", output / "gateware/flash_image.hex")

    output = build_and_run(root=ROOT, chapter="12-spi-flash",
        soc=lambda p: ProjectSoC(p, rom_words=words), regions=REGIONS,
        expected="SOC_COMPLETE data=0x0000005a", post_build_check=place_image,
        log_check=check_log)
    gateware = output / "gateware"
    flash_hex = gateware / "flash_image.hex"
    good_image = flash_hex.read_text()
    corrupted = bytearray(content)
    corrupted[8] ^= 1  # Keep the header intact; make the stored checksum wrong.
    try:
        flash_hex.write_text("".join(f"{byte:02x}\n" for byte in corrupted))
        bad = subprocess.run([str(gateware / "obj_dir/Vsim")], cwd=gateware,
                             capture_output=True, text=True, timeout=30)
    finally:
        flash_hex.write_text(good_image)
    bad_log = bad.stdout + bad.stderr
    (result / "corrupt-image.log").write_text(bad_log)
    if bad.returncode or "SOC_COMPLETE data=0x000000e3" not in bad_log or \
            "SOC_COMPLETE data=0x0000005a" in bad_log:
        raise AssertionError("损坏镜像没有被 CPU 校验和检查拒绝；查看 corrupt-image.log")
    print("EXPECTED_FAIL 12-FLASH-CHECKSUM: 镜像数据翻转 1 bit，CPU 报 0xe3")
    print(f"PASS 12-SPI-FLASH: 256-byte 镜像、4 KiB 窗口，校验和 0x{checksum:08x}")


if __name__ == "__main__":
    main()
