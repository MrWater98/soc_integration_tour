#!/usr/bin/env python3
"""Build chapter 09 firmware, simulate real LiteX UART pins, check byte order."""
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import shutil
import subprocess
import sys

CHAPTER = Path(__file__).resolve().parent
ROOT = CHAPTER.parent.parent if CHAPTER.parent.name == "chapters" else CHAPTER
sys.path.insert(0, str(ROOT))
from tour_paths import add_litex_to_path
from litex_builder import build_and_run, check_generated_map

REGIONS = {"rom": (0, 4096), "sram": (0x10000000, 4096),
           "main_ram": (0x40000000, 16384),
           "completion": (0x80000000, 4096), "csr": (0xf0000000, 65536)}
REGISTERS = {
    "uart_rxtx": (0xf0000800, "rw"), "uart_txfull": (0xf0000804, "ro"),
    "uart_rxempty": (0xf0000808, "ro"), "uart_ev_status": (0xf000080c, "ro"),
    "uart_ev_pending": (0xf0000810, "rw"), "uart_ev_enable": (0xf0000814, "rw"),
    "uart_txempty": (0xf0000818, "ro"), "uart_rxfull": (0xf000081c, "ro"),
}
TX_BYTES = b"UHELLO1234566"


def check_serial_log(log):
    def captured(prefix):
        return bytes(int(line.split("=0x", 1)[1], 16) for line in log.splitlines()
                     if line.startswith(prefix))
    tx = captured("UART_TX_BYTE value=0x")
    rx = captured("UART_RX_BYTE value=0x")
    if tx != TX_BYTES or rx != TX_BYTES:
        raise AssertionError(f"字节序错误: TX={tx!r}, RX={rx!r}, 期望={TX_BYTES!r}")
    for byte in TX_BYTES:
        tx_event = f"UART_TX_BYTE value=0x{byte:02x}"
        rx_event = f"UART_RX_BYTE value=0x{byte:02x}"
        if log.find(tx_event) > log.find(rx_event):
            raise AssertionError(f"CPU 在引脚完成发送之前报告收到 0x{byte:02x}")
    if "UART_FRAME_ERROR" in log:
        raise AssertionError("TX 引脚出现错误停止位")
    if "UART_FIFO_FULL seen=0x00000001" not in log:
        raise AssertionError("固件未观察到 TX FIFO 满")


def main():
    add_litex_to_path(ROOT)
    import litex
    from litex.build.generic_platform import Pins, Subsignal
    from litex.build.sim import SimPlatform
    from litex.build.io import CRG
    from litex.soc.integration.builder import Builder
    from soc import ProjectSoC, BIT_CYCLES

    result = ROOT / "results/09"
    image = result / "firmware"
    image.mkdir(parents=True, exist_ok=True)
    platform = SimPlatform("LITEX_TUTORIAL", [("sys_clk", 0, Pins(1)),
        ("serial", 0, Subsignal("tx", Pins(1)), Subsignal("rx", Pins(1)))])
    soc = ProjectSoC(platform, rom_words=[0x0000006f])
    soc.crg = CRG(platform.request("sys_clk"))
    soc.finalize()
    builder = Builder(soc, output_dir=str(result / "builder"),
                      compile_software=False, build_log=True)
    with (result / "elaborate.log").open("w") as log:
        with redirect_stdout(log), redirect_stderr(log):
            builder._generate_includes(with_bios=False)
            builder._generate_csr_map()
    header = result / "builder/software/include/generated/csr.h"
    check_generated_map(result / "builder/csr.csv", regions=REGIONS, registers=REGISTERS)
    (result / "csr-header.txt").write_text(header.read_text())

    gcc = shutil.which("riscv64-unknown-elf-gcc")
    objcopy = shutil.which("riscv64-unknown-elf-objcopy")
    if not gcc or not objcopy:
        raise RuntimeError("缺少第 00 章的 RISC-V gcc/objcopy")
    litex_root = Path(litex.__file__).resolve().parents[1]
    elf = image / "program.elf"
    command = [gcc, "-march=rv32i2p0", "-mabi=ilp32", "-mno-relax", "-ffreestanding",
        "-fno-builtin", "-nostdlib", "-nostartfiles", "-O1",
        "-I", str(header.parents[1]),
        "-I", str(litex_root / "litex/soc/cores/cpu/vexriscv"),
        "-I", str(litex_root / "litex/soc/software/include"),
        f"-Wl,-T,{CHAPTER / 'linker.ld'}", "-Wl,--build-id=none",
        f"-Wl,-Map={image / 'program.map'}",
        str(CHAPTER / "startup.S"), str(CHAPTER / "main.c"), "-o", str(elf)]
    built = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (image / "link.log").write_text(built.stdout + built.stderr)
    if built.returncode:
        raise RuntimeError(f"UART 固件编译失败：{built.stderr}")
    subprocess.run([objcopy, "-O", "binary", str(elf), str(image / "program.bin")],
                   check=True, timeout=30)
    data = (image / "program.bin").read_bytes()
    data += b"\0" * (-len(data) % 4)
    if len(data) > 4096:
        raise RuntimeError(f"ROM 镜像超限：{len(data)} bytes")
    words = [int.from_bytes(data[i:i+4], "little") for i in range(0, len(data), 4)]
    (image / "program.hex").write_text("".join(f"{word:08x}\n" for word in words))
    build_and_run(root=ROOT, chapter="09", soc=lambda p: ProjectSoC(p, rom_words=words),
        expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS, registers=REGISTERS,
        log_check=check_serial_log)
    try:
        build_and_run(root=ROOT, chapter="09-wrong-baud",
            soc=lambda p: ProjectSoC(p, rom_words=words,
                                      monitor_bit_cycles=BIT_CYCLES + 2),
            expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS,
            registers=REGISTERS, log_check=check_serial_log)
    except AssertionError as exc:
        (result / "wrong-baud.log").write_text(f"EXPECTED_FAIL 09-WRONG-BAUD: {exc}\n")
        print(f"EXPECTED_FAIL 09-WRONG-BAUD: {exc}")
    else:
        raise AssertionError("错误波特率的外部监视器不应解码出正确字节")
    def check_reset_log(log):
        markers = ("UART_RESET_TRIGGER: TX start bit",
                   "UART_RESET_ASSERT: frame incomplete", "UART_RESET_RELEASE",
                   "UART_TX_BYTE value=0x55", "SOC_COMPLETE data=0x0000005a")
        position = -1
        for marker in markers:
            position = log.find(marker, position + 1)
            if position < 0:
                raise AssertionError(f"传输中复位后缺少事件: {marker}")
        check_serial_log(log)

    build_and_run(root=ROOT, chapter="09-reset-tx",
        soc=lambda p: ProjectSoC(p, rom_words=words, reset_during_tx=True),
        expected="SOC_COMPLETE data=0x0000005a", regions=REGIONS,
        registers=REGISTERS, log_check=check_reset_log)
    print("PASS 09-UART: TX 引脚解码 UHELLO1234566；CPU 回显末字节，观察到 FIFO 满")


if __name__ == "__main__":
    main()
