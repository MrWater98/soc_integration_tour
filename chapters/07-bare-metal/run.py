#!/usr/bin/env python3
from pathlib import Path
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from baremetal import compile_image
from litex_builder import build_and_run


def check_ram_prefill(output):
    lines = (output / "gateware/sim_main_ram.init").read_text().splitlines()
    if len(lines) != 4096 or any(line.lower() != "a5a5a5a5" for line in lines):
        raise AssertionError("main RAM 仿真初值不是完整的 16 KiB 非零哨兵")


def main():
    add_litex_to_path(ROOT)
    from vexii_config import configure_vexii
    configure_vexii()
    from soc import ProjectSoC
    chapter = CHAPTER
    # Negative test: sections plus stack reserve cannot fit in 256 bytes.
    bad_dir, _, bad_rc = compile_image(ROOT, chapter, "07/small-ram", 256,
                                    source_names=("startup.S", "main.c"))
    negative_detail = (bad_dir / "link.log").read_text()
    if bad_rc == 0 or "main RAM has no room" not in negative_detail:
        raise AssertionError("256-byte main RAM was expected to fail the linker ASSERT")
    (ROOT / "results/07/small-ram/negative.log").write_text(
        "EXPECTED_FAIL: linker rejects insufficient main RAM\n" + negative_detail)
    print("EXPECTED_FAIL 07-SMALL-RAM: 链接器拒绝 256-byte main RAM")

    image_dir, words, link_rc = compile_image(ROOT, chapter, "07/firmware", 16 * 1024,
                                    source_names=("startup.S", "main.c"))
    if link_rc:
        raise RuntimeError(f"正常 main RAM 链接失败：{(image_dir / 'link.log').read_text()}")
    disassembly = (image_dir / "disassembly.txt").read_text()
    if "<use_stack>:" not in disassembly or "<stack_roundtrip>:" not in disassembly:
        raise AssertionError("编译器没有保留本章要观察的两层函数调用")
    roundtrip = disassembly.split("<stack_roundtrip>:", 1)[1].split("\n\n", 1)[0]
    if "sw\tra," not in roundtrip or "lw\tra," not in roundtrip:
        raise AssertionError("stack_roundtrip 未在栈中保存并恢复返回地址 ra")
    build_and_run(root=ROOT, chapter="07",
        expected="SOC_COMPLETE word_address=0x200003ff data=0x0000005a sel=f",
        soc=lambda platform: ProjectSoC(platform, rom_words=words,
                                         integrated_main_ram_size=16 * 1024,
                                         main_ram_init=[0xa5a5a5a5] * 4096),
        regions={"rom": (0, 4096), "sram": (0x10000000, 4096),
                 "main_ram": (0x40000000, 16384),
                 "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536),
                 "clint": (0xf0010000, 65536), "plic": (0xf0c00000, 4194304)},
        post_build_check=check_ram_prefill)
    print(f"ELF: {image_dir / 'program.elf'}; ROM image: {len(words) * 4} bytes")
    print("检查物: program.map、sections.txt、disassembly.txt、memory_map.csv、run.log")


if __name__ == "__main__":
    main()
