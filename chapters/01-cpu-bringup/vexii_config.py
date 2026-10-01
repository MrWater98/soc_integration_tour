"""Configure LiteX's native VexiiRiscv wrapper for the RV32 integration SoC."""
import argparse


def configure_vexii():
    from litex.soc.cores.cpu.vexiiriscv.core import VexiiRiscv

    parser = argparse.ArgumentParser(add_help=False)
    VexiiRiscv.args_fill(parser)
    args = parser.parse_args(["--update-repo=no"])
    args.cpu_variant = "standard"
    VexiiRiscv.args_read(args)
