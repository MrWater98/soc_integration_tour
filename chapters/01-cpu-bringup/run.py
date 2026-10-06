#!/usr/bin/env python3
"""Run a real VexRiscv fetch/store and a missing-ACK case."""
from pathlib import Path
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC
    regions = {"rom": (0, 64), "write_target": (0x40, 64),
               "csr": (0xf0000000, 65536)}
    output = build_and_run(root=ROOT, chapter="01", soc=lambda p: ProjectSoC(p),
        regions=regions, expected="PASS 01: VexRiscv wrote 0x40 to byte address 0x40",
        required_order=("FETCH first_byte_address=0x00000000", "PASS 01:"))
    output = build_and_run(root=ROOT, chapter="01-no-ack", soc=lambda p: ProjectSoC(p, no_ack=True),
        regions=regions, expected="PASS 01-NO-ACK: write request waited without ACK",
        required_order=("FETCH first_byte_address=0x00000000", "DATA_WAIT"))


if __name__ == "__main__":
    main()
