"""Compile this chapter's RV32 program and pack its ROM image."""
from pathlib import Path
import shutil
import subprocess
import hashlib

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent

def build_program(chapter: Path, *, build_name="build", defines=()):
    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("Required tools: riscv64-unknown-elf-gcc and riscv64-unknown-elf-objcopy")
    out = ROOT / "results" / build_name
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        gcc, "-march=rv32i2p0", "-mabi=ilp32", "-mno-relax", "-nostdlib", "-nostartfiles",
        "-Wl,--build-id=none", "-Wl,-Ttext=0", "-Wl,-e,_start",
        *(f"-D{name}" for name in defines),
        str(chapter / "program.S"), "-o", str(out / "program.elf"),
    ], check=True, timeout=30)
    subprocess.run([objcopy, "-O", "binary", str(out / "program.elf"), str(out / "program.bin")], check=True, timeout=30)
    raw_data = (out / "program.bin").read_bytes()
    data = raw_data
    if not data or len(data) % 4:
        data += b"\0" * ((4 - len(data) % 4) % 4)
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (out / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    (out / "program.sha256").write_text(f"{hashlib.sha256(raw_data).hexdigest()}  program.bin\n")
    decoded = b"".join(word.to_bytes(4, "little") for word in words)
    if decoded != data:
        raise AssertionError("ROM .hex and .bin little-endian packing mismatch")
    return out, len(words)


def write_rom_init(out: Path, depth: int, *, last_word=None):
    """Make a full, reproducible ROM image from the compact firmware image."""
    words = [int(line, 16) for line in (out / "program.hex").read_text().splitlines()]
    if len(words) > depth or (last_word is not None and len(words) >= depth):
        raise ValueError(f"Program uses {len(words)} words，ROM capacity {depth} words, exceeding capacity")
    words.extend([0] * (depth - len(words)))
    if last_word is not None:
        words[-1] = last_word
    init_text = "".join(f"{word:08x}\n" for word in words)
    (out / "rom_init.hex").write_text(init_text)
    (out / "rom_init.sha256").write_text(
        f"{hashlib.sha256(init_text.encode()).hexdigest()}  rom_init.hex\n")
    return words
