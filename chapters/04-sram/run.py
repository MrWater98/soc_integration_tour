#!/usr/bin/env python3
"""Boot native VexRiscv and exercise a chapter-local Wishbone SRAM."""
from pathlib import Path
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from cpu_sim import build_program, write_rom_init
from litex_builder import build_and_run


def regions(size):
    return {"rom": (0, 1024), "onchip_sram": (0x10000, size),
            "registers": (0x20000000, 4096), "csr": (0xf0000000, 65536)}


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    out, count = build_program(CHAPTER, build_name="04")
    if count > 256:
        raise ValueError("Program exceeds 1 KiB ROM")
    words = write_rom_init(out, 256, fill_word=0x00000013)
    build_and_run(root=ROOT, chapter="04", expected="SOC_COMPLETE data=0xbbcc33aa",
        soc=lambda p: ProjectSoC(p, rom_words=words, sram_size=4096,
            expected=0xbbcc33aa, finish_at_first=True), regions=regions(4096))
    build_and_run(root=ROOT, chapter="04-small-ram", expected="PASS SRAM_OOB_WAIT byte_address=0x00010ffc",
        soc=lambda p: ProjectSoC(p, rom_words=words, sram_size=256,
            expected=0xbbcc33aa, finish_at_first=True),
        regions=regions(256))
    print(f"PASS 04: ROM {count} words; SRAM first/last word, stack, and out-of-range no-response observed")


if __name__ == "__main__":
    main()
