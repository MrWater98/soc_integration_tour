#!/usr/bin/env python3
"""Run all three independent external-memory demonstrations."""
from pathlib import Path
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent


def main():
    for name in ("async-sram", "sdram", "spi-flash"):
        print(f"\n=== 12 {name} ===", flush=True)
        subprocess.run([sys.executable, str(CHAPTER / name / "run.py")],
                       check=True, timeout=360)
    print("PASS 12-MEMORY: 异步 SRAM、LiteDRAM SDRAM、SPI Flash 三项均通过")


if __name__ == "__main__":
    main()
