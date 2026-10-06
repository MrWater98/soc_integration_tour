#!/usr/bin/env python3
"""Check hand-written decode map, then boot VexRiscv against it."""
from pathlib import Path
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from cpu_sim import build_program, write_rom_init
from litex_builder import build_and_run

REGIONS = {"rom": (0, 4096), "onchip_sram": (0x10000, 4096),
           "registers": (0x20000000, 4096), "csr": (0xf0000000, 65536)}


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    subprocess.run([sys.executable, str(CHAPTER / "memory_map.py")], check=True, timeout=10)
    out, count = build_program(CHAPTER, build_name="05")
    if count > 1024:
        raise ValueError("Program exceeds ROM capacity")
    words = write_rom_init(out, 1024, last_word=0x5a6b7c8d)
    build_and_run(root=ROOT, chapter="05", expected="SOC_COMPLETE data=0x0000005a",
        soc=lambda p: ProjectSoC(p, rom_words=words, sram_size=4096), regions=REGIONS)
    bad_out, bad_count = build_program(CHAPTER, build_name="05-unmapped",
        defines=("UNMAPPED_CASE",))
    if bad_count > 1024:
        raise ValueError("Negative-case program exceeds ROM capacity")
    bad_words = write_rom_init(bad_out, 1024, last_word=0x5a6b7c8d)
    build_and_run(root=ROOT, chapter="05-unmapped", expected="PASS UNMAPPED_WAIT byte_address=0x30000000",
        soc=lambda p: ProjectSoC(p, rom_words=bad_words, sram_size=4096, unmapped_case=True), regions=REGIONS)
    print("PASS 05-DECODE: ROM, SRAM and register regions selected; unmapped load produced no response")


if __name__ == "__main__":
    main()
