"""Compile a linked bare-metal ELF and turn its ROM load image into LiteX words."""
import shutil
import subprocess
from pathlib import Path


def compile_image(root, chapter, name, main_ram_size, *, source_names):
    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    objdump = shutil.which("riscv64-unknown-elf-objdump")
    readelf = shutil.which("riscv64-unknown-elf-readelf")
    if not all((gcc, objcopy, objdump, readelf)):
        raise RuntimeError("第 00 章 RISC-V 工具链需提供 gcc/objcopy/objdump/readelf")
    out = root / "results" / name
    out.mkdir(parents=True, exist_ok=True)
    for filename in ("program.elf", "program.map", "program.bin", "program.hex",
                     "sections.txt", "disassembly.txt"):
        (out / filename).unlink(missing_ok=True)
    elf = out / "program.elf"
    command = [gcc, "-march=rv32i2p0", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        f"-Wl,-T,{chapter / 'linker.ld'}", f"-Wl,--defsym=MAIN_RAM_LENGTH={main_ram_size}",
        "-Wl,--build-id=none", f"-Wl,-Map={out / 'program.map'}", "-Wl,--print-memory-usage",
        *(str(chapter / source) for source in source_names), "-o", str(elf)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (out / "link.log").write_text(result.stdout + result.stderr)
    if result.returncode:
        return out, None, result.returncode
    (out / "sections.txt").write_text(subprocess.run([readelf, "-S", str(elf)],
        check=True, capture_output=True, text=True).stdout)
    (out / "disassembly.txt").write_text(subprocess.run([objdump, "-d", "-h", str(elf)],
        check=True, capture_output=True, text=True).stdout)
    subprocess.run([objcopy, "-O", "binary", str(elf), str(out / "program.bin")],
                   check=True, timeout=30)
    data = (out / "program.bin").read_bytes()
    data += b"\0" * ((-len(data)) % 4)
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (out / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    if len(data) > 0x1000:
        raise RuntimeError(f"启动 ROM 镜像 {len(data)} bytes 超过 4096 bytes")
    return out, words, 0
