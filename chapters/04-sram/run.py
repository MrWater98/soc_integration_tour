#!/usr/bin/env python3
"""Boot native VexiiRiscv and exercise a chapter-local Wishbone SRAM."""
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
            "registers": (0x20000000, 4096), "csr": (0xf0000000, 65536),
            "clint": (0xf0010000, 65536), "plic": (0xf0c00000, 4194304)}


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    from soc import ProjectSoC
    out, count = build_program(CHAPTER, build_name="04")
    if count > 256:
        raise ValueError("Program exceeds 1 KiB ROM")
    words = write_rom_init(out, 256, fill_word=0x00000013)
    build_and_run(root=ROOT, chapter="04", expected="SOC_COMPLETE data=0xbbcc33aa",
        soc=lambda p: ProjectSoC(p, rom_words=words, sram_size=4096,
            expected=0xbbcc33aa, finish_at_first=True), regions=regions(4096))
    build_and_run(root=ROOT, chapter="04-small-ram", expected="SOC_FAULT code=0xe1",
        soc=lambda p: ProjectSoC(p, rom_words=words, sram_size=256,
            expected=0xbbcc33aa, finish_at_first=True),
        regions=regions(256))
    fault_log = (ROOT / "results/04-small-ram/run.log").read_text()
    if "FAULT_CAUSE mcause=0x00000007" not in fault_log:
        raise AssertionError("Undersized SRAM did not report the expected store access fault")
    print(f"PASS 04: ROM {count} words; SRAM first/last word, stack, and store fault verified")


if __name__ == "__main__":
    main()
