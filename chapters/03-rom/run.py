#!/usr/bin/env python3
"""Compile a complete ROM image, then boot it on native VexRiscv."""
from pathlib import Path
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from cpu_sim import build_program, write_rom_init
from litex_builder import build_and_run

ROM_WORDS = 256


def validate_rom_image(word_count):
    if not 0 < word_count <= ROM_WORDS:
        raise ValueError(f"ROM image length {word_count} words is outside the range 1..{ROM_WORDS}")


def validate_reset_address(address):
    if address % 4 or not 0 <= address < ROM_WORDS * 4:
        raise ValueError(f"Reset address 0x{address:08x} is unaligned or outside the ROM range")


def rejection(label, fn):
    try:
        fn()
    except ValueError as exc:
        return f"PASS {label}: {exc}"
    raise AssertionError(f"{label}: Invalid configuration was not rejected")


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    out, count = build_program(CHAPTER, build_name="03")
    validate_rom_image(count)
    validate_reset_address(0)
    words = write_rom_init(out, ROM_WORDS, fill_word=0x00000013)
    messages = [rejection("03-EMPTY-ROM", lambda: validate_rom_image(0)),
        rejection("03-OVERSIZE-ROM", lambda: validate_rom_image(ROM_WORDS + 1)),
        rejection("03-WRONG-RESET-CONFIG", lambda: validate_reset_address(0x1000)),
        rejection("03-MISALIGNED-RESET", lambda: validate_reset_address(1))]
    (out / "config.log").write_text("\n".join(messages) + "\n")
    print("\n".join(messages))
    output = build_and_run(root=ROOT, chapter="03", soc=lambda p: ProjectSoC(p,
        rom_words=words, expected=0x35, finish_at_first=True),
        expected="SOC_COMPLETE data=0x00000035",
        regions={"rom": (0, 1024), "registers": (0x20000000, 4096),
                 "csr": (0xf0000000, 65536)})
    print(f"ROM image: {count} program words / {ROM_WORDS} total words")


if __name__ == "__main__":
    main()
