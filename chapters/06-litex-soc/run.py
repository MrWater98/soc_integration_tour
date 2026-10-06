#!/usr/bin/env python3
from pathlib import Path
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from cpu_sim import build_program, write_rom_init
from litex_builder import build_and_run, check_generated_map


def reject_stale_map(output):
    """Reject firmware addresses from the pre-SoCCore memory map."""
    try:
        check_generated_map(output / "csr.csv", regions={
            "rom": (0, 4096), "sram": (0x00010000, 4096),
            "completion": (0x20000000, 4096), "csr": (0xf0000000, 65536)})
    except AssertionError:
        detail = ("EXPECTED_FAIL 06-STALE-MAP: previous map uses SRAM=0x00010000, "
                  "completion=0x20000000; Builder maps SRAM=0x10000000, "
                  "completion=0x80000000. Firmware must be relinked.\n")
        (ROOT / "results/06/stale-map.log").write_text(detail)
        print(detail.strip())
    else:
        raise AssertionError("The prior hand-written memory map must be rejected by the generated-map check")


def main():
    add_litex_to_path(ROOT)
    from soc import ProjectSoC, COMPLETION_CODE
    out, word_count = build_program(CHAPTER, build_name="06/firmware")
    if word_count * 4 > 0x1000:
        raise SystemExit(f"ROM image ({word_count * 4} bytes) exceeds the 4096-byte ROM")
    words = write_rom_init(out, 1024, last_word=0x5a6b7c8d)
    build_and_run(root=ROOT, chapter="06",
        expected="SOC_COMPLETE word_address=0x200003ff data=0x0000005a sel=f",
        soc=lambda platform: ProjectSoC(platform, rom_words=words),
        regions={"rom": (0, 4096), "sram": (0x10000000, 4096),
                 "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536)},
        post_build_check=reject_stale_map)
    print(f"Firmware image: {out / 'program.hex'} ({word_count * 4} bytes)")
    print(f"Completion code: 0x{COMPLETION_CODE:02x}")


if __name__ == "__main__":
    main()
