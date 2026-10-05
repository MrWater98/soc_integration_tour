#!/usr/bin/env python3
"""Run a real VexiiRiscv fetch/store and a missing-ACK case."""
from pathlib import Path
import shutil
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    from soc import ProjectSoC
    regions = {"rom": (0, 64), "write_target": (0x40, 64),
               "csr": (0xf0000000, 65536), "clint": (0xf0010000, 65536),
               "plic": (0xf0c00000, 4194304)}
    output = build_and_run(root=ROOT, chapter="01", soc=lambda p: ProjectSoC(p),
        regions=regions, expected="PASS 01: VexiiRiscv wrote 0x40 to byte address 0x40",
        required_order=("FETCH first_byte_address=0x00000000", "PASS 01:"))
    rtl_dir = CHAPTER / "work" / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(output / "gateware" / "sim.v", rtl_dir / "01-normal.v")
    output = build_and_run(root=ROOT, chapter="01-no-ack", soc=lambda p: ProjectSoC(p, no_ack=True),
        regions=regions, expected="PASS 01-NO-ACK: write request waited without ACK",
        required_order=("FETCH first_byte_address=0x00000000", "DATA_WAIT"))
    shutil.copyfile(output / "gateware" / "sim.v", rtl_dir / "01-no-ack.v")


if __name__ == "__main__":
    main()
