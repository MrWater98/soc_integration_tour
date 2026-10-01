"""Readable byte-address map and overlap checks for chapter 05."""
from dataclasses import dataclass
import csv
from pathlib import Path

@dataclass(frozen=True)
class Region:
    name: str
    base: int
    size: int
    access: str
    responder: str = "unassigned"

    @property
    def end(self):
        return self.base + self.size - 1

REGIONS = (
    Region("rom", 0x00000000, 0x1000, "read-only", "soc.rom"),
    Region("sram", 0x00010000, 0x1000, "read-write", "soc.onchip_sram"),
    Region("registers", 0x20000000, 0x1000, "read-write", "soc.registers"),
)

def validate(regions):
    if not regions:
        raise ValueError("Address map cannot be empty")
    for region in regions:
        if region.base < 0 or region.size <= 0 or region.base % 4 or region.size % 4:
            raise ValueError(f"{region.name}: base and size must be non-negative, non-zero and 4-byte aligned")
    ordered = sorted(regions, key=lambda region: region.base)
    for left, right in zip(ordered, ordered[1:]):
        if left.end >= right.base:
            raise ValueError(f"Address overlap: {left.name} ends at 0x{left.end:08x}, {right.name} starts at 0x{right.base:08x}")
    return ordered

def decode(regions, byte_address):
    hits = [region for region in regions if region.base <= byte_address <= region.end]
    if len(hits) > 1:
        raise ValueError(f"Address 0x{byte_address:08x} matches multiple regions")
    return hits[0] if hits else None

if __name__ == "__main__":
    regions = validate(REGIONS)
    for region in regions:
        print(f"{region.name:10} 0x{region.base:08x}..0x{region.end:08x} {region.access}")
    chapter = Path(__file__).resolve().parent
    root = chapter.parent.parent if chapter.parent.name == "chapters" else chapter
    output = root / "results/05/memory_map.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("name", "base_byte", "base_word", "size_bytes", "end_byte", "end_word", "access", "cache_policy", "responder"))
        for region in regions:
            writer.writerow((region.name, f"0x{region.base:08x}", f"0x{region.base // 4:08x}",
                             region.size, f"0x{region.end:08x}", f"0x{region.end // 4:08x}",
                             region.access, "uncached" if region.name == "registers" else "cached", region.responder))
    (output.parent / "irq_map.csv").write_text("irq_number,source\n")
    try:
        validate((*REGIONS, Region("bad", 0x00000ffc, 0x100, "read-write")))
    except ValueError as exc:
        print(f"PASS 05-OVERLAP: {exc}")
    else:
        raise SystemExit("FAIL: Overlapping address regions were not rejected")
    assert decode(REGIONS, 0x00000000).name == "rom"
    assert decode(REGIONS, 0x00000ffc).name == "rom"
    assert decode(REGIONS, 0x00010000).name == "sram"
    assert decode(REGIONS, 0x00010ffc).name == "sram"
    assert decode(REGIONS, 0x20000000).name == "registers"
    assert decode(REGIONS, 0x20000ffc).name == "registers"
    assert decode(REGIONS, 0x30000000) is None
    print("PASS 05-MAP: first and last addresses select one region; unmapped address selects none")
    print(f"Wrote memory map: {output}")
